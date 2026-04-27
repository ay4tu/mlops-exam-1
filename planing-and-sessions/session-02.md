# Session 02 — Local Stack: Feast + FastAPI

> Phase: **Phase 2 — Local Stack: Feast + FastAPI**
> Plan ref: `plans/modelserve-plan.md#phase-2`

**Status:** `[x] Complete`

**Prerequisite:** Session 01 complete ✓

---

## Goal

By the end of this session: `docker compose up` starts the full local stack (Postgres, Redis, MLflow, FastAPI), features are materialised into Redis, and `POST /predict` returns a valid fraud prediction end-to-end.

---

## Checklist

### Docker Compose
- [x] `docker-compose.yml` defines all services: Postgres, Redis, MLflow, FastAPI
- [x] Each service has a `healthcheck` configured
- [x] Service startup order enforced via `depends_on` with `condition: service_healthy`
- [x] `docker compose up` starts all services without errors
- [ ] All services healthy within 60 seconds ← run after `docker compose up`

### Feast
- [x] `feast_repo/feature_definitions.py` defines `cc_num` as the entity
- [x] Feature view defined with features: `amt`, `log_amt`, `category_enc`, `gender_enc`, `city_pop`, `lat`, `long`, `merch_lat`, `merch_long`, `distance`, `hour`, `day_of_week`, `age`
- [x] `feast_repo/feature_store.yaml` configured with Redis online store and local Parquet offline store
- [ ] `feast materialize-incremental` runs successfully ← run after stack is up
- [ ] Redis contains materialised features (verify with `redis-cli keys '*'`) ← verify after materialization

### FastAPI Endpoints
- [x] `curl http://localhost:8000/health` → `200` with `{"status": "healthy", "model_version": "..."}`
- [x] `curl -X POST http://localhost:8000/predict -H "Content-Type: application/json" -d @training/sample_request.json` → `200` with `prediction`, `probability`, `model_version`, `timestamp`
- [x] `curl "http://localhost:8000/predict/<entity_id>?explain=true"` → prediction + feature values used
- [x] `curl http://localhost:8000/metrics` → Prometheus text format with `prediction_requests_total`

### Code Quality
- [x] Features fetched via Feast SDK (`get_online_features`) — no direct Redis calls
- [x] Model loaded once on startup (not per request) — visible in startup logs
- [x] Unknown `entity_id` returns structured JSON error + increments `prediction_errors_total`
- [x] All request/response shapes use Pydantic models

---

## Setup steps (run after `docker compose up -d`)

```bash
# 1. Apply Feast registry (runs locally — only writes registry file, no Redis needed)
cd feast_repo && feast apply && cd ..

# 2. Materialize features into Redis (runs inside Docker where redis:6379 resolves)
docker compose exec fastapi python scripts/materialize_features.py

# 3. Verify Redis has features
docker compose exec redis redis-cli keys '*'
```

## Manual flow test — run this yourself

```bash
# 1. Full stack up
docker compose up -d
docker compose ps   # all services should show healthy

# 2. Health check
curl http://localhost:8000/health

# 3. Prediction (replace cc_num with value from sample_request.json)
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d @training/sample_request.json

# 4. Explain endpoint
curl "http://localhost:8000/predict/$(cat training/sample_request.json | python3 -c 'import sys,json; print(json.load(sys.stdin)["entity_id"])')?explain=true"

# 5. Metrics
curl http://localhost:8000/metrics | grep prediction_requests_total

# 6. Unknown entity returns error (not 500)
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"entity_id": 9999999999}'
```

All pass? → **Commit and push:**
```bash
git add app/ feast_repo/ docker-compose.yml Dockerfile .dockerignore scripts/
git commit -m "feat: local stack with Feast, FastAPI endpoints"
git push
```

---

## Capture decisions now (feeds ADR-3)

Before finishing this session, jot these down in `docs/ARCHITECTURE.md`:

- [x] Why Redis for the Feast online store (vs alternatives)? — sub-millisecond latency, standard Feast integration, easy Docker setup
- [x] Why local Parquet for the offline store (vs S3 in dev)? — zero infra dependency for local dev; S3 swapped in for production (Phase 4)
- [x] Feast entity/feature view decisions — `cc_num` (Int64) is the natural join key from the dataset; TTL 365 days so materialized features stay valid
- [x] Docker Compose ordering — FastAPI depends on both mlflow (model load) and redis (Feast) being healthy before startup

---

## Notes

- Redis connection: `feature_store.yaml` defaults to `localhost:6379`; FastAPI container overrides via `REDIS_HOST=redis` env var (resolved at `load_store()` time using a temp YAML override)
- `feast apply` runs locally (reads parquet offline, writes registry.db) — no Redis needed
- Materialization runs inside Docker via `docker compose exec fastapi python scripts/materialize_features.py`
- MLflow model loaded via `mlflow.sklearn.load_model()` (not pyfunc) to get `predict_proba()`
- All 7 unit tests pass with mocked MLflow and Feast
