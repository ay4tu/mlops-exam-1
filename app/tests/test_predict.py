import numpy as np
import pandas as pd
import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

MOCK_ENTITY_ID = 2703186189652095
FEATURE_COLS = [
    "amt", "log_amt", "category_enc", "gender_enc", "city_pop",
    "lat", "long", "merch_lat", "merch_long", "distance",
    "hour", "day_of_week", "age",
]
MOCK_FEATURES = pd.DataFrame([{col: 1.0 for col in FEATURE_COLS}])


def _make_mock_sklearn():
    m = MagicMock()
    m.predict_proba.return_value = np.array([[0.1, 0.9]])
    return m


@pytest.fixture(scope="module")
def client():
    mock_sklearn = _make_mock_sklearn()

    import app.model_loader as ml
    import app.feature_client as fc

    def setup_model():
        ml._model = mock_sklearn
        ml._model_version = "42"

    def mock_get_features(entity_id: int):
        if entity_id == MOCK_ENTITY_ID:
            return MOCK_FEATURES
        return None

    with (
        patch.object(ml, "load_model", side_effect=setup_model),
        patch.object(fc, "load_store"),
        patch.object(fc, "get_features", mock_get_features),
    ):
        from app.main import app
        with TestClient(app) as c:
            yield c


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "healthy"
    assert "model_version" in body


def test_predict_valid_entity(client):
    resp = client.post("/predict", json={"entity_id": MOCK_ENTITY_ID})
    assert resp.status_code == 200
    body = resp.json()
    assert body["prediction"] in (0, 1)
    assert 0.0 <= body["probability"] <= 1.0
    assert "model_version" in body
    assert "timestamp" in body


def test_predict_unknown_entity_returns_404(client):
    resp = client.post("/predict", json={"entity_id": 9999999999})
    assert resp.status_code == 404
    body = resp.json()
    assert body["detail"]["error"] == "entity_not_found"


def test_predict_invalid_input_returns_422(client):
    resp = client.post("/predict", json={"entity_id": "not-an-int"})
    assert resp.status_code == 422


def test_predict_explain(client):
    resp = client.get(f"/predict/{MOCK_ENTITY_ID}?explain=true")
    assert resp.status_code == 200
    body = resp.json()
    assert body["prediction"] in (0, 1)
    assert isinstance(body["features"], dict)
    assert "amt" in body["features"]


def test_predict_explain_unknown_entity(client):
    resp = client.get("/predict/9999999999?explain=true")
    assert resp.status_code == 404


def test_metrics_endpoint(client):
    resp = client.get("/metrics")
    assert resp.status_code == 200
    assert "prediction_requests_total" in resp.text
