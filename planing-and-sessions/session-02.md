# Session 02 — Local Stack: Feast + FastAPI

> Phase: **Phase 2 — Local Stack: Feast + FastAPI**
> Plan ref: `plans/modelserve-plan.md#phase-2`

**Status:** `[ ] Not Started`

**Prerequisite:** Session 01 complete ✓

---

## Goal

By the end of this session: `docker compose up` starts the full local stack (Postgres, Redis, MLflow, FastAPI), features are materialised into Redis, and `POST /predict` returns a valid fraud prediction end-to-end.

---

## Checklist

### Docker Compose
- [ ] `docker-compose.yml` defines all services: Postgres, Redis, MLflow, FastAPI
- [ ] Each service has a `healthcheck` configured
- [ ] Service startup order enforced via `depends_on` with `condition: service_healthy`
- [ ] `docker compose up` starts all services without errors
- [ ] All services healthy within 60 seconds

### Feast
- [ ] `feast_repo/feature_definitions.py` defines `cc_num` as the entity
- [ ] Feature view defined with features: `amt`, `category` (encoded), `city_pop`, `lat`, `long`, `merch_lat`, `merch_long`, `hour_of_day`, `day_of_week`, `age`
- [ ] `feast_repo/feature_store.yaml` configured with Redis online store and local Parquet offline store
- [ ] `feast materialize-incremental` runs successfully
- [ ] Redis contains materialised features (verify with `redis-cli keys '*'`)

### FastAPI Endpoints
- [ ] `curl http://localhost:8000/health` → `200` with `{"status": "healthy", "model_version": "..."}`
- [ ] `curl -X POST http://localhost:8000/predict -H "Content-Type: application/json" -d @training/sample_request.json` → `200` with `prediction`, `probability`, `model_version`, `timestamp`
- [ ] `curl "http://localhost:8000/predict/<entity_id>?explain=true"` → prediction + feature values used
- [ ] `curl http://localhost:8000/metrics` → Prometheus text format with `prediction_requests_total`

### Code Quality
- [ ] Features fetched via Feast SDK (`get_online_features`) — no direct Redis calls
- [ ] Model loaded once on startup (not per request) — visible in startup logs
- [ ] Unknown `entity_id` returns structured JSON error + increments `prediction_errors_total`
- [ ] All request/response shapes use Pydantic models
- [ ] All changes pushed to GitHub

---

## Notes

<!-- Add any blockers, decisions made, or deviations from the plan here -->
