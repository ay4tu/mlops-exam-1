# Session 06 — Cloud Deployment: EC2 Bootstrap & Stack Up

> Phase: **Phase 4 — Pulumi Cloud Infrastructure** (part 2)
> Plan ref: `plans/modelserve-plan.md#phase-4`

**Status:** `[ ] Not Started`

**Prerequisite:** Session 05 complete ✓

---

## Goal

By the end of this session: the full ModelServe stack (FastAPI, MLflow, Feast, Redis, Postgres, Prometheus, Grafana) is running on the EC2 instance provisioned by Pulumi, and predictions are accessible from the public Elastic IP.

---

## Checklist

### EC2 Bootstrap Script
- [ ] User-data script installs Docker and Docker Compose on EC2 instance
- [ ] User-data script pulls the repository from GitHub on first boot
- [ ] User-data script runs `docker compose up -d` automatically
- [ ] Bootstrap completes in under 10 minutes (demo constraint)
- [ ] Script is idempotent (safe to re-run)

### MLflow Artifact Store (S3)
- [ ] EC2 IAM role has read/write access to the S3 bucket
- [ ] `docker-compose.yml` production variant configures MLflow to use S3 artifact store
- [ ] MLflow can store and retrieve artifacts from S3 (verify by re-running `train.py` or pushing an existing model artifact)

### ECR Image Push
- [ ] FastAPI Docker image built and tagged for ECR
- [ ] Image pushed to ECR repository: `docker push <ecr-url>/modelserve-api:latest`
- [ ] EC2 instance can pull image from ECR (IAM role allows `ecr:GetAuthorizationToken`, `ecr:BatchGetImage`)

### End-to-End on EC2
- [ ] `curl http://<elastic-ip>:8000/health` returns 200 from local machine
- [ ] `curl -X POST http://<elastic-ip>:8000/predict -d @training/sample_request.json` returns valid prediction
- [ ] `curl http://<elastic-ip>:5000` loads MLflow UI (model in Production stage visible)
- [ ] `curl http://<elastic-ip>:3000` loads Grafana dashboard
- [ ] `curl http://<elastic-ip>:9090` loads Prometheus UI (FastAPI target UP)
- [ ] Feast features materialised on EC2 (Redis populated)

### Cleanup
- [ ] `pulumi destroy --yes` removes all resources cleanly

---

## Manual flow test — run this yourself

```bash
# Replace <ip> with your Elastic IP from: pulumi stack output instance_ip

# 1. Health check from your local machine
curl http://<ip>:8000/health

# 2. Prediction from your local machine
curl -X POST http://<ip>:8000/predict \
  -H "Content-Type: application/json" \
  -d @training/sample_request.json

# 3. MLflow UI
open http://<ip>:5000

# 4. Grafana dashboard
open http://<ip>:3000

# 5. Prometheus targets
open http://<ip>:9090/targets
```

All pass? → **Commit and push:**
```bash
git add infrastructure/ docker-compose.yml scripts/
git commit -m "feat: full stack deployed to EC2 via Pulumi"
git push
```

---

## Notes

<!-- Add any blockers, decisions made, or deviations from the plan here -->
