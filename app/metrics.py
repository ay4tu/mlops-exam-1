from prometheus_client import Counter, Gauge, Histogram

prediction_requests_total = Counter(
    "prediction_requests_total",
    "Total number of prediction requests",
)

prediction_duration_seconds = Histogram(
    "prediction_duration_seconds",
    "Time to process each prediction",
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0],
)

prediction_errors_total = Counter(
    "prediction_errors_total",
    "Number of failed prediction requests",
)

model_version_info = Gauge(
    "model_version_info",
    "Currently served model version",
    labelnames=["version"],
)

feast_online_store_hits_total = Counter(
    "feast_online_store_hits_total",
    "Successful feature lookups from Feast",
)

feast_online_store_misses_total = Counter(
    "feast_online_store_misses_total",
    "Failed or empty feature lookups from Feast",
)
