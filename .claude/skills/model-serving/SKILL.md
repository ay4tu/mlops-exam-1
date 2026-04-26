---
name: model-serving
description: Implement and debug the full MLOps model-serving stack: training script, experiment tracking, feature store, inference API, and observability. Use when building or fixing any layer of a model-serving system — train.py, MLflow registration, Feast feature definitions, FastAPI endpoints, Prometheus metrics, or Docker/Compose setup.
---

# Model Serving

Build or debug a production ML serving stack end-to-end.

## Workflow

### 1. Understand the task

Read the session tracker or plan file to identify which layer is in scope. Explore the relevant files before touching anything. If the task spans multiple layers, confirm the scope with the user.

### 2. Training & experiment tracking

1. Write a training script that loads data, engineers features, trains a model, and logs to the tracker
2. Log all params, metrics, and the model artifact — nothing undocumented
3. Register the model in the registry and promote it to the production stage
4. Export the feature file (Parquet) and a valid test request payload (JSON)

Verify: registry UI shows the model in production stage with logged metrics.

### 3. Feature store

1. Define the entity and feature view in the feature store config
2. Point the offline store at the exported feature file
3. Point the online store at the cache (Redis or equivalent)
4. Materialise features into the online store

Verify: online store contains keys for entities in the test payload.

### 4. Inference API

Implement endpoints in this order — each must work before moving to the next:

1. `GET /health` — returns service status and current model version
2. `GET /metrics` — returns Prometheus-format metrics
3. `POST /predict` — fetches features from the feature store, runs the model, returns prediction
4. `GET /predict/<id>?explain=true` — same as above but also returns the feature values used

Rules:
- Load the model once at startup, not per request
- Fetch features through the feature store SDK, never via direct cache queries
- All errors return structured JSON with an appropriate HTTP status code
- Increment error metrics on every failure path

Verify: curl against each endpoint returns the expected shape.

### 5. Observability

1. Define the four required Prometheus metrics: request counter, duration histogram, error counter, model version gauge
2. Instrument every code path that handles a request
3. Add Prometheus and Grafana to Docker Compose
4. Provision the Grafana datasource and dashboard from config files — no manual UI steps

Verify: Grafana dashboard renders with live data after sending a burst of requests.

### 6. Validate

Run all checks before marking a session complete:

```
docker compose up        # full stack starts cleanly
curl /health             # 200 with model version
curl /predict            # valid prediction response
curl /metrics            # Prometheus text with all four metrics
```

Fix any failures before moving to the next session.
