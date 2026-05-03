# Session 06 — Cloud Deployment: EC2 Bootstrap & Stack Up

> Phase: **Phase 4 — Pulumi Cloud Infrastructure** (part 2)
> Plan ref: `plans/modelserve-plan.md#phase-4`

**Status:** `[✓] Complete`

**Prerequisite:** Session 05 complete ✓

---

## Goal

By the end of this session: the full ModelServe stack (FastAPI, MLflow, Feast, Redis, Postgres, Prometheus, Grafana) is running on the EC2 instance provisioned by Pulumi, and predictions are accessible from the public Elastic IP.

---

## Checklist

### EC2 Bootstrap Script
- [x] User-data script installs Docker and Docker Compose on EC2 instance
- [x] User-data script pulls the repository from GitHub on first boot
- [x] User-data script runs `docker compose up -d` automatically
- [x] Bootstrap completes in under 10 minutes (demo constraint)
- [x] Script is idempotent (safe to re-run)

### MLflow Artifact Store (S3)
- [x] EC2 IAM role has read/write access to the S3 bucket
- [x] `docker-compose.prod.yml` configures MLflow to use S3 artifact store
- [x] MLflow can store and retrieve artifacts from S3 (verified via `train.py` → S3)

### ECR Image Push
- [x] FastAPI Docker image built and tagged for ECR
- [x] Image pushed to ECR repository via `scripts/push-to-ecr.sh`
- [x] EC2 instance can pull image from ECR (IAM role confirmed working)

### End-to-End on EC2
- [x] `curl http://<elastic-ip>:8000/health` returns 200 from local machine
- [x] `curl -X POST http://<elastic-ip>:8000/predict -d @training/sample_request.json` returns valid prediction
- [x] `curl http://<elastic-ip>:5000` loads MLflow UI (model in Production stage visible)
- [x] `curl http://<elastic-ip>:3000` loads Grafana dashboard
- [x] `curl http://<elastic-ip>:9090` loads Prometheus UI (FastAPI target UP)
- [x] Feast features materialised on EC2 (Redis populated — 983 keys)

### Cleanup
- [ ] `pulumi destroy --yes` removes all resources cleanly

---

## Deploy flow (established this session)

```bash
# Fresh session — two commands only
cd infrastructure && pulumi up --yes && cd ..
./scripts/deploy.sh   # build → push → restart stack → train → feast apply → materialize
```

### What deploy.sh does
1. Builds FastAPI image for linux/amd64 and pushes to ECR
2. SSHs into EC2, runs `docker-compose down` then `up`
3. Calls `scripts/seed-model.sh`:
   - Trains locally with `MLFLOW_TRACKING_URI=http://<EC2-IP>:5000`
   - SCPs `features.parquet` to EC2
   - Runs `feast apply` + `materialize_features.py` on EC2 container

### Key decisions made
- Training runs **locally** (not on EC2) — avoids OOM on t3.medium
- Model artifacts stored in **S3** via EC2 MLflow
- Feast materialization uses **Python script** (`scripts/materialize_features.py`) not CLI — CLI ignores REDIS_HOST env var
- FastAPI has **retry loop** (18×10s) on model load — survives fresh deploys

---

## Notes

- `docker-compose` (v2 standalone) is installed on EC2, not the Docker plugin — use `docker-compose` not `docker compose`
- `feast materialize-incremental` with wrong start timestamp materializes 0 rows — use `scripts/materialize_features.py` instead which hardcodes the 2019 start date
- EC2 is t3.medium (upgraded from t3.small) — OOM with full 1.3M row training, hence local training
