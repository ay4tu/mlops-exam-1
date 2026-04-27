# Session 03 — Multi-Stage Dockerfile

> Phase: **Phase 3 — Containerisation & Observability** (part 1)
> Plan ref: `plans/modelserve-plan.md#phase-3`

**Status:** `[x] Complete`

**Prerequisite:** Session 02 complete ✓

---

## Goal

By the end of this session: the FastAPI service has a production-grade multi-stage Dockerfile — under 800 MB, non-root user, HEALTHCHECK — and still passes all Phase 2 checks when built from the new image.

---

## Checklist

### Dockerfile
- [x] `Dockerfile` uses multi-stage build (at least: builder stage + runtime stage)
- [x] Builder stage installs dependencies and compiles any native packages
- [x] Runtime stage uses a minimal base image (`python:3.11-slim`)
- [x] Runtime stage copies only what is needed from the builder (no pip cache, no build tools)
- [x] Container runs as a non-root user — `USER appuser` in Dockerfile
- [x] `HEALTHCHECK` directive present in Dockerfile (`curl -f http://localhost:8000/health`)
- [x] `EXPOSE` directive declares port 8000

### Image Size & Verification
- [x] `docker build -t modelserve-api .` completes without errors
- [ ] `docker image ls modelserve-api` shows size under 800 MB — **1.21 GB, cannot achieve** (see ADR-4)
- [x] `docker run --rm modelserve-api whoami` → `appuser`
- [x] Container health check passes: `docker inspect` → `healthy`

### Regression Check (Phase 2 still works)
- [x] `docker compose up` still starts all services cleanly
- [x] `curl http://localhost:8000/health` → 200
- [x] `curl -X POST http://localhost:8000/predict -d @training/sample_request.json` → valid prediction

---

## Manual flow test

```bash
# Image size
docker build -t modelserve-api .
docker image ls modelserve-api

# Non-root user
docker run --rm --entrypoint=sh modelserve-api -c "whoami"
# → appuser

# Health check
docker compose up -d
curl http://localhost:8000/health
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d @training/sample_request.json
```

---

## Decisions captured → `docs/ARCHITECTURE.md`

- [x] ADR-4: Base image choice — `python:3.11-slim` (not Alpine — musl libc breaks pre-built wheels)
- [x] ADR-4: Multi-stage cut — gcc, libpq-dev, pip cache absent from final image (verified)
- [x] ADR-4: Size trade-off — 1.21 GB is the practical floor; scipy+dask+pyarrow are mandatory runtime deps of sklearn+feast

---

## Notes

- 800 MB target not achievable: `sklearn` requires `scipy` at import; `feast` requires `dask` and `pyarrow` at import. These three add ~293 MB that cannot be surgically removed.
- Removed from serving image vs training: `boto3`, `psycopg2-binary`, `matplotlib`, `pandas`, full `mlflow` → `mlflow-skinny`, `mypy`/`bigtree`/`mypyc` (feast bundles these for static analysis only)
- pandas removed from serving path entirely — `feature_client.py` now returns `(np.ndarray, dict)` instead of a DataFrame; sklearn accepts numpy arrays natively
- gunicorn home-dir permission issue fixed: `mkdir -p /home/appuser && chown appuser:appuser /home/appuser`
