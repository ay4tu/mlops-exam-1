import logging
import os
import tempfile
from pathlib import Path
from typing import Optional

import numpy as np
import yaml

from app.metrics import feast_online_store_hits_total, feast_online_store_misses_total

log = logging.getLogger(__name__)

FEATURE_REFS = [
    "transaction_features:amt",
    "transaction_features:log_amt",
    "transaction_features:category_enc",
    "transaction_features:gender_enc",
    "transaction_features:city_pop",
    "transaction_features:lat",
    "transaction_features:long",
    "transaction_features:merch_lat",
    "transaction_features:merch_long",
    "transaction_features:distance",
    "transaction_features:hour",
    "transaction_features:day_of_week",
    "transaction_features:age",
]

FEATURE_COLS = [
    "amt", "log_amt", "category_enc", "gender_enc", "city_pop",
    "lat", "long", "merch_lat", "merch_long", "distance",
    "hour", "day_of_week", "age",
]

_store = None


def load_store():
    global _store
    from feast import FeatureStore

    repo_path = Path(__file__).parent.parent / "feast_repo"
    redis_host = os.getenv("REDIS_HOST", "localhost")
    redis_port = os.getenv("REDIS_PORT", "6379")

    yaml_path = repo_path / "feature_store.yaml"
    config = yaml.safe_load(yaml_path.read_text())
    config["online_store"]["connection_string"] = f"{redis_host}:{redis_port}"

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", delete=False, dir=repo_path
    ) as f:
        yaml.dump(config, f)
        tmp_path = Path(f.name)

    try:
        _store = FeatureStore(repo_path=str(repo_path), fs_yaml_file=tmp_path)
        log.info("Feast store loaded, project: %s, redis: %s:%s", _store.project, redis_host, redis_port)
    finally:
        tmp_path.unlink(missing_ok=True)


def get_features(entity_id: int) -> Optional[tuple[np.ndarray, dict]]:
    try:
        response = _store.get_online_features(
            features=FEATURE_REFS,
            entity_rows=[{"cc_num": entity_id}],
        ).to_dict()

        # None values mean the entity was not found in the online store
        if any(v[0] is None for k, v in response.items() if k != "cc_num" and isinstance(v, list) and v):
            feast_online_store_misses_total.inc()
            log.warning("No features found for entity_id=%s", entity_id)
            return None

        feast_online_store_hits_total.inc()
        row = {k: v[0] for k, v in response.items() if k != "cc_num"}
        arr = np.array([[row[col] for col in FEATURE_COLS]], dtype=np.float64)
        return arr, row

    except Exception as e:
        feast_online_store_misses_total.inc()
        log.error("Feature fetch error for entity_id=%s: %s", entity_id, e)
        return None
