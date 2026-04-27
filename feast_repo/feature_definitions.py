from datetime import timedelta
from pathlib import Path

from feast import Entity, FeatureView, Field, FileSource
from feast.types import Float64, Int64

REPO_DIR = Path(__file__).parent
FEATURES_PATH = str(REPO_DIR.parent / "training" / "features.parquet")

cc_num = Entity(name="cc_num", description="Credit card number")

transaction_source = FileSource(
    path=FEATURES_PATH,
    timestamp_field="event_timestamp",
)

transaction_features = FeatureView(
    name="transaction_features",
    entities=[cc_num],
    ttl=timedelta(days=365),
    schema=[
        Field(name="amt", dtype=Float64),
        Field(name="log_amt", dtype=Float64),
        Field(name="category_enc", dtype=Int64),
        Field(name="gender_enc", dtype=Int64),
        Field(name="city_pop", dtype=Int64),
        Field(name="lat", dtype=Float64),
        Field(name="long", dtype=Float64),
        Field(name="merch_lat", dtype=Float64),
        Field(name="merch_long", dtype=Float64),
        Field(name="distance", dtype=Float64),
        Field(name="hour", dtype=Int64),
        Field(name="day_of_week", dtype=Int64),
        Field(name="age", dtype=Float64),
    ],
    source=transaction_source,
)
