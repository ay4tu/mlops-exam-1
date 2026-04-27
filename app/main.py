import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from pydantic import BaseModel

from app import feature_client, model_loader
from app.metrics import (
    model_version_info,
    prediction_duration_seconds,
    prediction_errors_total,
    prediction_requests_total,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    model_loader.load_model()
    feature_client.load_store()
    model_version_info.labels(version=model_loader.get_model_version()).set(1)
    log.info("Startup complete — model v%s", model_loader.get_model_version())
    yield


app = FastAPI(lifespan=lifespan)


class PredictRequest(BaseModel):
    entity_id: int


class PredictResponse(BaseModel):
    prediction: int
    probability: float
    model_version: str
    timestamp: str


class PredictExplainResponse(PredictResponse):
    features: dict


@app.get("/health")
def health():
    return {"status": "healthy", "model_version": model_loader.get_model_version()}


@app.post("/predict", response_model=PredictResponse)
def predict(req: PredictRequest):
    prediction_requests_total.inc()
    with prediction_duration_seconds.time():
        features = feature_client.get_features(req.entity_id)
        if features is None:
            prediction_errors_total.inc()
            raise HTTPException(
                status_code=404,
                detail={"error": "entity_not_found", "entity_id": req.entity_id},
            )
        try:
            prob = model_loader.predict_proba(features)
            pred = int(prob > 0.5)
        except Exception as e:
            prediction_errors_total.inc()
            log.error("Prediction error for entity_id=%s: %s", req.entity_id, e)
            raise HTTPException(status_code=500, detail={"error": "prediction_failed"})

    return PredictResponse(
        prediction=pred,
        probability=prob,
        model_version=model_loader.get_model_version(),
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


@app.get("/predict/{entity_id}", response_model=PredictExplainResponse)
def predict_explain(entity_id: int, explain: bool = False):
    prediction_requests_total.inc()
    with prediction_duration_seconds.time():
        features = feature_client.get_features(entity_id)
        if features is None:
            prediction_errors_total.inc()
            raise HTTPException(
                status_code=404,
                detail={"error": "entity_not_found", "entity_id": entity_id},
            )
        try:
            prob = model_loader.predict_proba(features)
            pred = int(prob > 0.5)
        except Exception as e:
            prediction_errors_total.inc()
            log.error("Prediction error for entity_id=%s: %s", entity_id, e)
            raise HTTPException(status_code=500, detail={"error": "prediction_failed"})

    return PredictExplainResponse(
        prediction=pred,
        probability=prob,
        model_version=model_loader.get_model_version(),
        timestamp=datetime.now(timezone.utc).isoformat(),
        features=features.iloc[0].to_dict() if explain else {},
    )


@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
