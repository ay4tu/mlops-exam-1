import logging
import os

log = logging.getLogger(__name__)

_model = None
_model_version = "unknown"


def load_model():
    import mlflow
    import mlflow.sklearn

    global _model, _model_version
    tracking_uri = os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5001")
    model_name = os.getenv("MODEL_NAME", "fraud-detector")
    model_stage = os.getenv("MODEL_STAGE", "Production")

    mlflow.set_tracking_uri(tracking_uri)
    log.info("Loading model %s/%s from %s", model_name, model_stage, tracking_uri)

    model_uri = f"models:/{model_name}/{model_stage}"
    _model = mlflow.sklearn.load_model(model_uri)

    client = mlflow.MlflowClient()
    versions = client.get_latest_versions(model_name, stages=[model_stage])
    _model_version = str(versions[0].version) if versions else "unknown"
    log.info("Model loaded: %s v%s", model_name, _model_version)


def get_model_version() -> str:
    return _model_version


def predict_proba(features) -> float:
    proba = _model.predict_proba(features)[:, 1]
    return float(proba[0])
