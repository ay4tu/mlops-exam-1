# Plan: ModelServe

> Source PRD: `plans/modelserve-prd.md`

## Architectural Decisions

Durable decisions that apply across all phases:

- **Entity key**: `cc_num` (integer) — used as `entity_id` in the API and as the Feast entity
- **API routes**: `GET /health`, `POST /predict`, `GET /predict/<entity_id>`, `GET /metrics`, `GET /rollback`
- **ML task**: Binary classification (`is_fraud` 0/1), sklearn-compatible model with `class_weight='balanced'`
- **Feature store**: Feast with Redis online store, local Parquet offline store
- **Experiment tracking**: MLflow with PostgreSQL backend, S3 artifact store (production) / local volume (dev)
- **Deployment topology**: Single AWS EC2 instance (`t3.small`), all containers via Docker Compose
- **Infrastructure**: Pulumi (Python), incremental update strategy (`pulumi up` — not destroy-and-recreate)
- **CI/CD triggers**: `test` on every push + PR; `build-and-push` + `deploy` on push to `main` AND version tags (`v*.*.*`)
- **Bonus targets**: Trivy scan (+2), Pulumi PR preview (+2), `/rollback` endpoint (+2)

---

## Phase 1: Model & MLflow Foundation

**User stories**: 1, 2, 3, 4, 5, 6, 7

### What to build

Write `training/train.py` that loads `fraudTrain.csv`, engineers features, trains a baseline fraud classifier, logs everything to MLflow, registers the model as `Production`, and exports the two artefacts downstream components depend on: `features.parquet` (for Feast) and `sample_request.json` (for API testing). At the end of this phase MLflow UI shows a registered Production model with metrics and the two export files exist on disk.

### Acceptance criteria

- [ ] `fraudTrain.csv` downloaded to `data/` (gitignored)
- [ ] `docker compose up postgres mlflow` starts cleanly with no errors
- [ ] `python training/train.py` runs to completion without errors
- [ ] MLflow UI at `http://localhost:5000` shows at least one experiment run with logged parameters and metrics (accuracy, precision, recall, F1, ROC-AUC)
- [ ] A model named `fraud-detector` exists in the MLflow Model Registry with at least one version in the `Production` stage
- [ ] `training/features.parquet` exists and contains `cc_num`, `event_timestamp`, and at least 5 feature columns
- [ ] `training/sample_request.json` exists and contains `{"entity_id": <valid cc_num from dataset>}`
- [ ] Running `python training/train.py` a second time registers a new version with comparable metrics (reproducibility check)
- [ ] Model ROC-AUC ≥ 0.85 on the test split

---

## Phase 2: Local Stack — Feast + FastAPI

**User stories**: 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 23, 24

### What to build

Build the full local development stack. Write `docker-compose.yml` with Postgres, Redis, MLflow, and FastAPI wired together with health checks and correct startup order. Write Feast feature definitions keyed on `cc_num` and materialise the online store from `features.parquet`. Implement the FastAPI service (`app/main.py`, `app/model_loader.py`, `app/feature_client.py`, `app/metrics.py`) with all four endpoints. At the end of this phase `docker compose up` brings up the entire stack and predictions are served end-to-end.

### Acceptance criteria

- [ ] `docker compose up` starts all services (Postgres, Redis, MLflow, FastAPI) without errors
- [ ] All services pass their health checks within 60 seconds of `docker compose up`
- [ ] Feast feature definitions exist in `feast_repo/feature_definitions.py` with `cc_num` as the entity
- [ ] `feast materialize-incremental` runs successfully and populates Redis
- [ ] `curl http://localhost:8000/health` returns `200` with `{"status": "healthy", "model_version": "<version>"}`
- [ ] `curl -X POST http://localhost:8000/predict -H "Content-Type: application/json" -d @training/sample_request.json` returns `200` with `prediction`, `probability`, `model_version`, and `timestamp`
- [ ] `curl "http://localhost:8000/predict/<entity_id>?explain=true"` returns prediction plus the feature values used
- [ ] `curl http://localhost:8000/metrics` returns Prometheus text format containing `prediction_requests_total`
- [ ] Features are fetched through the Feast SDK (`get_online_features`) — no direct Redis calls
- [ ] Model is loaded once on startup, not on each request (verify via startup logs)
- [ ] A request with an unknown `entity_id` returns structured JSON error with an appropriate HTTP status code and increments `prediction_errors_total`
- [ ] All request/response shapes validated by Pydantic models

---

## Phase 3: Containerisation & Observability

**User stories**: 20, 21, 22, 25, 26, 27, 28, 29

### What to build

Write a multi-stage `Dockerfile` for the FastAPI service that produces a small, secure image. Add Prometheus and Grafana to `docker-compose.yml`. Write Prometheus config to scrape FastAPI. Write three alert rules. Provision the Grafana datasource and dashboard from files so no manual UI setup is needed. At the end of this phase the full stack starts with monitoring in one `docker compose up` and the dashboard shows live data.

### Acceptance criteria

- [ ] `Dockerfile` uses multi-stage build (builder stage + runtime stage)
- [ ] Final FastAPI image size is under 800 MB (`docker image ls`)
- [ ] Container runs as a non-root user (verify with `docker exec <container> whoami`)
- [ ] `Dockerfile` contains a `HEALTHCHECK` directive
- [ ] `docker compose up` starts Prometheus and Grafana alongside all existing services
- [ ] Prometheus at `http://localhost:9090` shows the FastAPI target as `UP` (check Targets page)
- [ ] Grafana at `http://localhost:3000` loads the dashboard automatically without any manual configuration
- [ ] Grafana dashboard shows panels for: latency p50/p95/p99, request rate, error rate, model version, Feast hit/miss ratio
- [ ] `monitoring/prometheus/alerts.yml` defines at least three alert rules: high latency, high error rate, service down
- [ ] All three alert rules are visible in the Prometheus UI at `/alerts`
- [ ] After sending 10+ requests, all dashboard panels show non-zero data

---

## Phase 4: Pulumi Cloud Infrastructure

**User stories**: 30, 31, 32, 33, 34, 35

### What to build

Write `infrastructure/__main__.py` to provision the full AWS environment: VPC, public subnet, security group, EC2 instance with user-data bootstrap script, Elastic IP, S3 bucket, and ECR repository. Deploy the full stack to EC2 and verify end-to-end predictions work from the public IP. At the end of this phase the system is accessible from the internet and `pulumi destroy` cleans up everything.

### Acceptance criteria

- [ ] `cd infrastructure && pulumi up --yes` completes without errors
- [ ] All resources are tagged with `Project: modelserve` (verify in AWS console or via CLI)
- [ ] Pulumi stack exports: EC2 public IP, ECR repository URL, S3 bucket name
- [ ] EC2 instance is `t3.small` running in a public subnet with an Elastic IP
- [ ] Security group allows inbound on ports: 22 (SSH, restricted CIDR), 8000 (FastAPI), 3000 (Grafana), 5000 (MLflow), 9090 (Prometheus) — and nothing else
- [ ] ECR repository has `force_delete=True` so images don't block destroy
- [ ] `curl http://<elastic-ip>:8000/health` returns 200 from your local machine
- [ ] `curl -X POST http://<elastic-ip>:8000/predict -d @training/sample_request.json` returns a valid prediction
- [ ] `curl http://<elastic-ip>:3000` loads Grafana login page
- [ ] `curl http://<elastic-ip>:5000` loads MLflow UI
- [ ] `pulumi destroy --yes` removes all provisioned resources cleanly (no orphaned resources)
- [ ] MLflow artifact store is configured to use S3 in production

---

## Phase 5: GitHub Actions CI/CD

**User stories**: 36, 37, 38, 39, 40, 41, 42, 43

### What to build

Write `.github/workflows/deploy.yml` with five jobs: `test`, `build-and-push`, `deploy`, `trivy-scan`, and `pulumi-preview`. Wire triggers so tests run on every push/PR, the full pipeline runs on push to `main` and version tags, and Pulumi preview comments on PRs. Store all credentials in GitHub Secrets. At the end of this phase a push to `main` triggers a complete test → build → deploy cycle and the service is verified live.

### Acceptance criteria

- [ ] All required GitHub Secrets configured: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION`, `EC2_HOST`, `EC2_SSH_KEY`, `ECR_REPOSITORY`
- [ ] `test` job runs on every push to `main` and every PR — pytest passes
- [ ] `build-and-push` job runs on push to `main` and version tags (`v*.*.*`) — Docker image pushed to ECR
- [ ] `deploy` job runs after `build-and-push` — SSHes into EC2, pulls new image, restarts service
- [ ] `deploy` job verifies `/health` returns 200 after deployment — fails the job if not
- [ ] `trivy-scan` job scans the FastAPI image for critical CVEs and fails the pipeline if found
- [ ] `pulumi-preview` job runs on PRs and posts the Pulumi diff as a PR comment
- [ ] No credentials are hardcoded anywhere in `.github/workflows/deploy.yml`
- [ ] Pushing to `main` triggers the full workflow — all jobs show green checkmarks on GitHub
- [ ] After a successful pipeline run, `curl http://<elastic-ip>:8000/health` returns 200
- [ ] Pipeline can be re-run end-to-end without manual intervention between runs
- [ ] Creating a version tag (e.g. `git tag v1.0.0 && git push --tags`) triggers `build-and-push` + `deploy`

---

## Phase 6: Documentation, Bonus & Hardening

**User stories**: 19, 44, 45, 46, 47, 48, 49

### What to build

Write the full `docs/ARCHITECTURE.md` engineering document. Implement the `/rollback` endpoint. Polish the Grafana dashboard. Run a full cold-start rehearsal. At the end of this phase the repository is submission-ready: documentation complete, all acceptance criteria met, pipeline green, and the demo rehearsed.

### Acceptance criteria

**`/rollback` endpoint**
- [ ] `GET /rollback` switches the active model to the previous Production version in MLflow Registry
- [ ] Response confirms the new active model version
- [ ] The change is visible in the MLflow UI immediately after calling the endpoint
- [ ] Subsequent `/predict` calls use the rolled-back model version

**`docs/ARCHITECTURE.md`**
- [ ] System overview section: 2–3 paragraphs describing what the system does, who it serves, and the design philosophy
- [ ] Architecture diagram committed to `docs/diagrams/` and referenced in the markdown — shows every component, where it runs, ports, and communication paths
- [ ] Separate diagram for local development topology and production (EC2) topology
- [ ] ADR-1: Deployment topology (why single EC2, trade-offs)
- [ ] ADR-2: CI/CD strategy (why incremental update + hybrid trigger, when destroy-and-recreate is better)
- [ ] ADR-3: Data architecture (why Postgres for MLflow, Redis for Feast, S3 for artifacts)
- [ ] ADR-4: Containerisation (base image choice, multi-stage rationale, image size trade-offs)
- [ ] ADR-5: Monitoring design (alert threshold rationale, dashboard optimisation, what's missing)
- [ ] CI/CD pipeline documentation: each job described, triggers, secrets used, failure handling, expected deploy time
- [ ] Runbook covering: fresh-clone bootstrap, deploying a new model version, recovering from common failures (service crash, S3 permission loss, Pulumi state corruption), full teardown
- [ ] Known Limitations section: honest list of what the system does not handle

**`README.md`**
- [ ] Project description (2–3 sentences)
- [ ] Prerequisites listed (Docker, Python, AWS CLI, Pulumi, Kaggle API)
- [ ] Quick setup instructions for local development
- [ ] REST endpoint table (method, path, description, example response)
- [ ] Environment variable table with descriptions (matching `.env.example`)
- [ ] GitHub Secrets section listing every secret (without values)
- [ ] Link to `docs/ARCHITECTURE.md`

**Final submission checks**
- [ ] Repository is public on GitHub
- [ ] `docker compose up` from a fresh clone reaches healthy state in under 15 minutes
- [ ] Latest commit on `main` shows green checkmark on GitHub Actions
- [ ] `docs/ARCHITECTURE.md` is complete with all required sections
- [ ] `training/features.parquet` and `training/sample_request.json` are committed
- [ ] `.env.example` lists all required environment variables (without values)
- [ ] Demo rehearsed at least once: cold-start → pipeline → live predictions → Grafana → Q&A
