#!/usr/bin/env python3
"""Fraud detection model training, MLflow registration, and artefact export."""
import json
import logging
import os
from pathlib import Path

import mlflow
import mlflow.sklearn
import numpy as np
import pandas as pd
from mlflow import MlflowClient
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split

DATA_PATH = Path("data/fraudTrain.csv")
MODEL_NAME = "fraud-detector"
EXPERIMENT_NAME = "fraud-detection"
RANDOM_STATE = 42
TEST_SIZE = 0.2

FEATURE_COLS = [
    "amt",
    "log_amt",
    "category_enc",
    "gender_enc",
    "city_pop",
    "lat",
    "long",
    "merch_lat",
    "merch_long",
    "distance",
    "hour",
    "day_of_week",
    "age",
]

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["trans_date_trans_time"] = pd.to_datetime(df["trans_date_trans_time"])
    df["dob"] = pd.to_datetime(df["dob"])

    df["hour"] = df["trans_date_trans_time"].dt.hour
    df["day_of_week"] = df["trans_date_trans_time"].dt.dayofweek
    df["age"] = (df["trans_date_trans_time"] - df["dob"]).dt.days / 365.25
    df["distance"] = np.sqrt(
        (df["lat"] - df["merch_lat"]) ** 2 + (df["long"] - df["merch_long"]) ** 2
    )
    df["log_amt"] = np.log1p(df["amt"])

    # Deterministic integer encoding keyed on sorted unique values
    categories = sorted(df["category"].unique())
    cat_map = {c: i for i, c in enumerate(categories)}
    df["category_enc"] = df["category"].map(cat_map).astype(int)

    df["gender_enc"] = (df["gender"] == "M").astype(int)
    return df


def train():
    mlflow.set_tracking_uri(os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000"))
    mlflow.set_experiment(EXPERIMENT_NAME)

    log.info("Loading %s", DATA_PATH)
    df = pd.read_csv(DATA_PATH)
    log.info("Loaded %d rows", len(df))

    df = engineer_features(df)

    X = df[FEATURE_COLS]
    y = df["is_fraud"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=TEST_SIZE, random_state=RANDOM_STATE, stratify=y
    )

    log.info("Train=%d Test=%d", len(X_train), len(X_test))

    params = {
        "max_iter": 200,
        "max_depth": 8,
        "learning_rate": 0.1,
        "class_weight": "balanced",
        "random_state": RANDOM_STATE,
    }

    with mlflow.start_run():
        mlflow.log_params(params)
        mlflow.log_param("model_type", "HistGradientBoostingClassifier")
        mlflow.log_param("features", ",".join(FEATURE_COLS))
        mlflow.log_param("n_features", len(FEATURE_COLS))

        model = HistGradientBoostingClassifier(**params)
        log.info("Training HistGradientBoostingClassifier (%d iters)...", params["max_iter"])
        model.fit(X_train, y_train)

        y_pred = model.predict(X_test)
        y_prob = model.predict_proba(X_test)[:, 1]

        metrics = {
            "accuracy": round(float(accuracy_score(y_test, y_pred)), 4),
            "precision": round(float(precision_score(y_test, y_pred)), 4),
            "recall": round(float(recall_score(y_test, y_pred)), 4),
            "f1": round(float(f1_score(y_test, y_pred)), 4),
            "roc_auc": round(float(roc_auc_score(y_test, y_prob)), 4),
        }
        mlflow.log_metrics(metrics)
        log.info("Metrics: %s", metrics)

        if metrics["roc_auc"] < 0.85:
            raise ValueError(f"ROC-AUC {metrics['roc_auc']:.4f} < 0.85 — check features")

        mlflow.sklearn.log_model(
            model,
            artifact_path="model",
            registered_model_name=MODEL_NAME,
        )

    # Promote latest version to Production
    client = MlflowClient()
    versions = client.get_latest_versions(MODEL_NAME)
    latest = str(max(int(v.version) for v in versions))
    client.transition_model_version_stage(
        name=MODEL_NAME,
        version=latest,
        stage="Production",
        archive_existing_versions=True,
    )
    log.info("Model %s v%s → Production", MODEL_NAME, latest)

    # Export features.parquet for Feast (cc_num + event_timestamp + feature cols)
    feat_df = df[["cc_num", "trans_date_trans_time"] + FEATURE_COLS].rename(
        columns={"trans_date_trans_time": "event_timestamp"}
    )
    feat_path = Path("training/features.parquet")
    feat_df.to_parquet(feat_path, index=False)
    log.info("Exported %s — %d rows, %d cols", feat_path, len(feat_df), len(feat_df.columns))

    # Export sample_request.json
    sample_path = Path("training/sample_request.json")
    sample_path.write_text(json.dumps({"entity_id": int(df["cc_num"].iloc[0])}, indent=2))
    log.info("Exported %s", sample_path)


if __name__ == "__main__":
    train()
