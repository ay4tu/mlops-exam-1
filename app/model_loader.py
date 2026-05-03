import logging
import os
import time

log = logging.getLogger(__name__)

_model = None
_model_version = "unknown"

_RETRIES = int(os.getenv("MODEL_LOAD_RETRIES", "18"))
_RETRY_DELAY = int(os.getenv("MODEL_LOAD_RETRY_DELAY", "10"))


def load_model():
    import mlflow
    import mlflow.sklearn

    global _model, _model_version
    tracking_uri = os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5001")
    model_name = os.getenv("MODEL_NAME", "fraud-detector")
    model_stage = os.getenv("MODEL_STAGE", "Production")

    mlflow.set_tracking_uri(tracking_uri)
    model_uri = f"models:/{model_name}/{model_stage}"

    for attempt in range(1, _RETRIES + 1):
        try:
            log.info("Loading model %s/%s from %s (attempt %d/%d)",
                     model_name, model_stage, tracking_uri, attempt, _RETRIES)
            _model = mlflow.sklearn.load_model(model_uri)
            client = mlflow.MlflowClient()
            versions = client.get_latest_versions(model_name, stages=[model_stage])
            _model_version = str(versions[0].version) if versions else "unknown"
            log.info("Model loaded: %s v%s", model_name, _model_version)
            return
        except Exception as e:
            if attempt == _RETRIES:
                raise
            log.warning("Model not ready (attempt %d/%d): %s — retrying in %ds",
                        attempt, _RETRIES, e, _RETRY_DELAY)
            time.sleep(_RETRY_DELAY)


def get_model_version() -> str:
    return _model_version


def predict_proba(features) -> float:
    proba = _model.predict_proba(features)[:, 1]
    return float(proba[0])
