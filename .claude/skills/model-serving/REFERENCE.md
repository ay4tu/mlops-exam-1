# Model Serving — Reference

## Common failure patterns

| Symptom | Most likely cause | Fix |
|---|---|---|
| Model not found at startup | Model not in production stage, or registry URI wrong | Check env vars, check registry UI |
| Feature lookup returns empty | Online store not materialised | Re-run `feast materialize-incremental` |
| `/metrics` missing a counter | Metric not incremented on that code path | Instrument the error/success branch |
| Grafana shows no data | Dashboard JSON references wrong datasource UID | Check provisioned datasource name matches dashboard JSON |
| `pulumi destroy` fails on ECR | Images still in repository | Set `force_delete=True` on the ECR resource |

## Model loading pattern

Load once at module level or in a startup event — never inside the request handler:

```python
# On startup
model = registry.load_model(name, stage="Production")

# On request
prediction = model.predict(features)
```

## Feature store lookup pattern

Always go through the SDK, never query the cache directly:

```python
result = feature_store.get_online_features(
    features=["view:feature_a", "view:feature_b"],
    entity_rows=[{"entity_key": entity_id}]
).to_dict()
```

## Prometheus metrics — required four

```python
request_counter   = Counter("prediction_requests_total", "...", ["model_version"])
duration_hist     = Histogram("prediction_duration_seconds", "...")
error_counter     = Counter("prediction_errors_total", "...", ["error_type"])
version_gauge     = Gauge("model_version_info", "...", ["version"])
```

## Structured error response

```python
# Every error path
return JSONResponse(
    status_code=404,
    content={"error": "Entity not found", "detail": str(e)}
)
# And increment the error counter
error_counter.labels(error_type="not_found").inc()
```

## Docker Compose health check pattern

```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
  interval: 10s
  timeout: 5s
  retries: 5
```

Use `depends_on` with `condition: service_healthy` to enforce startup order.
