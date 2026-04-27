#!/usr/bin/env python3
"""Materialize features from offline parquet store into Redis online store."""
import logging
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import yaml

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)


def main():
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
        store = FeatureStore(repo_path=str(repo_path), fs_yaml_file=tmp_path)
    finally:
        tmp_path.unlink(missing_ok=True)

    # Dataset timestamps are 2019-2020; use a fixed start date to cover all data
    start_date = datetime(2019, 1, 1, tzinfo=timezone.utc)
    end_date = datetime.now(timezone.utc)
    log.info("Materializing features %s → %s (redis=%s:%s)", start_date, end_date, redis_host, redis_port)
    store.materialize(start_date=start_date, end_date=end_date)
    log.info("Materialization complete")


if __name__ == "__main__":
    main()
