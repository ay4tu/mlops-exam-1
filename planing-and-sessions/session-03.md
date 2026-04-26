# Session 03 — Multi-Stage Dockerfile

> Phase: **Phase 3 — Containerisation & Observability** (part 1)
> Plan ref: `plans/modelserve-plan.md#phase-3`

**Status:** `[ ] Not Started`

**Prerequisite:** Session 02 complete ✓

---

## Goal

By the end of this session: the FastAPI service has a production-grade multi-stage Dockerfile — under 800 MB, non-root user, HEALTHCHECK — and still passes all Phase 2 checks when built from the new image.

---

## Checklist

### Dockerfile
- [ ] `Dockerfile` uses multi-stage build (at least: builder stage + runtime stage)
- [ ] Builder stage installs dependencies and compiles any native packages
- [ ] Runtime stage uses a minimal base image (e.g. `python:3.11-slim`)
- [ ] Runtime stage copies only what is needed from the builder (no pip cache, no build tools)
- [ ] Container runs as a non-root user — `USER` directive in Dockerfile
- [ ] `HEALTHCHECK` directive present in Dockerfile
- [ ] `EXPOSE` directive declares the correct port

### Image Size & Verification
- [ ] `docker build -t modelserve-api .` completes without errors
- [ ] `docker image ls modelserve-api` shows size under 800 MB
- [ ] `docker run --rm modelserve-api whoami` outputs a non-root username
- [ ] Container health check passes: `docker inspect <container> | grep Health`

### Regression Check (Phase 2 still works)
- [ ] `docker compose up` still starts all services cleanly using the new image
- [ ] `curl http://localhost:8000/health` still returns 200
- [ ] `curl -X POST http://localhost:8000/predict -d @training/sample_request.json` still returns valid prediction

---

## Manual flow test — run this yourself

```bash
# 1. Check image size
docker build -t modelserve-api .
docker image ls modelserve-api

# 2. Confirm non-root user
docker run --rm modelserve-api whoami

# 3. Full stack still works
docker compose up -d
curl http://localhost:8000/health
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d @training/sample_request.json
```

All pass? → **Commit and push:**
```bash
git add Dockerfile
git commit -m "feat: multi-stage Dockerfile with non-root user and healthcheck"
git push
```

---

## Capture decisions now (feeds ADR-4)

Before finishing this session, jot these down in `docs/ARCHITECTURE.md`:

- [ ] Which base image did you choose for the runtime stage and why?
- [ ] What did the multi-stage build actually cut from the final image (size before vs after)?
- [ ] Any trade-offs you accepted (e.g. Alpine vs slim, specific Python version)?

---

## Notes

<!-- Add any blockers, decisions made, or deviations from the plan here -->
