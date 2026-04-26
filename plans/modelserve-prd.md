# PRD: ModelServe — Production ML Serving Platform

## Problem Statement

An ML engineer needs to take a trained fraud-detection model and wrap it in the full production infrastructure that makes it actually serveable at scale. Training a model locally is not enough — the model needs experiment tracking, versioned artifact storage, a feature store for consistent feature serving, a containerised inference API, end-to-end observability, cloud infrastructure provisioned as code, and an automated CI/CD pipeline that deploys new model versions without manual intervention. Without this infrastructure, the model cannot be reliably served, monitored, rolled back, or reproduced by another engineer.

## Solution

Build **ModelServe**: a production-grade ML serving platform that wraps a Credit Card Fraud Detection classifier (trained on the Kaggle `kartik2112/fraud-detection` dataset) in the full MLOps stack. The system exposes a FastAPI inference service that fetches features from a Feast online store (Redis), loads the production model from the MLflow Registry, and returns structured fraud predictions. All services are containerised with Docker, deployed to a single AWS EC2 instance provisioned by Pulumi, and continuously delivered through a GitHub Actions pipeline that triggers on push to `main` and on version tags.

The system is observable via Prometheus metrics and a Grafana dashboard, covers the full lifecycle from model training to live prediction, and is documented with an architecture diagram, five ADRs, a runbook, and a CI/CD pipeline description — enough for any engineer to understand, reproduce, and operate the platform without asking the author.

## User Stories

### Model Training & Registry

1. As an ML engineer, I want a reproducible `train.py` script, so that running it again produces a functionally equivalent model registered in MLflow.
2. As an ML engineer, I want the model trained on `fraudTrain.csv` with stratified splitting, so that class imbalance (`is_fraud` ~0.5%) is handled correctly via `class_weight='balanced'`.
3. As an ML engineer, I want training metrics (accuracy, precision, recall, F1, ROC-AUC) logged to MLflow, so that I can compare model versions objectively.
4. As an ML engineer, I want model hyperparameters and feature list logged to MLflow, so that any registered version is fully reproducible.
5. As an ML engineer, I want the trained model registered in the MLflow Model Registry and automatically transitioned to the `Production` stage, so that the inference service always loads the latest approved version.
6. As an ML engineer, I want `train.py` to export `features.parquet` from the training data, so that Feast can ingest features into the offline store.
7. As an ML engineer, I want `train.py` to export `sample_request.json` with a valid `cc_num` from the dataset, so that the inference service can be tested immediately after training.

### Feature Store

8. As a data engineer, I want Feast feature definitions written for the fraud detection features (amount, category, city population, lat/long distances, hour of day, day of week), so that features are consistently available for both training and serving.
9. As a data engineer, I want `features.parquet` ingested into the Feast offline store, so that the historical feature record is available for materialisation.
10. As a data engineer, I want features materialised into Redis via `feast materialize-incremental`, so that the online store is populated for low-latency serving.
11. As the inference service, I want to fetch features from Feast's online store using `feature_store.get_online_features(entity_rows=[{"cc_num": entity_id}])`, so that feature retrieval is consistent with training and does not bypass the feature store SDK.

### Inference API

12. As a client application, I want to call `GET /health` and receive `{"status": "healthy", "model_version": "<version>"}`, so that load balancers and CI pipelines can verify the service is up.
13. As a client application, I want to call `POST /predict` with `{"entity_id": <cc_num>}` and receive `{"prediction": <int>, "probability": <float>, "model_version": "<version>", "timestamp": "<iso8601>"}`, so that I can get a fraud verdict for any cardholder.
14. As a debugging engineer, I want to call `GET /predict/<entity_id>?explain=true` and receive the prediction plus the exact feature values used, so that I can audit why the model made a particular decision.
15. As a Prometheus scraper, I want `GET /metrics` to expose `prediction_requests_total`, `prediction_duration_seconds`, `prediction_errors_total`, and `model_version_info` in Prometheus text format, so that the full request lifecycle is observable.
16. As the inference service, I want the model loaded from the MLflow Registry exactly once at application startup, so that prediction latency is not inflated by repeated model downloads.
17. As the inference service, I want prediction errors to return structured JSON with appropriate HTTP status codes and to increment `prediction_errors_total`, so that failures are observable and client-friendly.
18. As a developer, I want Pydantic models for all request and response shapes, so that input validation is automatic and the API contract is self-documenting.
19. As the inference service, I want a `/rollback` endpoint that switches the active model to the previous Production version in the MLflow Registry, so that a bad deployment can be reverted live during the demo.

### Containerisation

20. As a DevOps engineer, I want a multi-stage Dockerfile for the FastAPI service, so that the final runtime image is under 800 MB and does not include build tools.
21. As a DevOps engineer, I want the FastAPI container to run as a non-root user, so that the principle of least privilege is followed.
22. As a DevOps engineer, I want the Dockerfile to include a `HEALTHCHECK` directive, so that Docker can self-report container health.
23. As a developer, I want `docker compose up` from the repo root to start MLflow, Postgres, Redis, FastAPI, Prometheus, and Grafana without any manual steps, so that the local development stack comes up in one command.
24. As a developer, I want all services to define `healthcheck` and `depends_on` with `condition: service_healthy`, so that services start in the correct order.

### Observability

25. As a platform engineer, I want Prometheus to scrape the FastAPI `/metrics` endpoint, so that all prediction activity is recorded.
26. As a platform engineer, I want a Grafana dashboard provisioned automatically from JSON on `docker compose up`, so that no manual Grafana configuration is required after startup.
27. As a platform engineer, I want the Grafana dashboard to show prediction latency p50/p95/p99, request rate, error rate, model version, and Feast hit/miss ratio, so that I can assess system health at a glance.
28. As an on-call engineer, I want at least three Prometheus alert rules — high latency, elevated error rate, and service-down — so that I am paged before customers notice a problem.
29. As an on-call engineer, I want alert thresholds documented with their rationale in the ARCHITECTURE.md, so that future engineers know why the thresholds were chosen.

### Cloud Infrastructure

30. As a DevOps engineer, I want Pulumi (Python) to provision a VPC, public subnet, security group, EC2 instance (t3.small), S3 bucket, and ECR repository, so that the full deployment target is created from code with a single `pulumi up`.
31. As a DevOps engineer, I want all Pulumi-provisioned resources tagged with `Project: modelserve`, so that cost attribution and cleanup are straightforward.
32. As a DevOps engineer, I want Pulumi to export stack outputs (EC2 IP, ECR URL, S3 bucket name), so that downstream CI/CD jobs can reference them without hardcoding.
33. As a DevOps engineer, I want `pulumi destroy --yes` to cleanly remove all provisioned resources including ECR images (via `force_delete=True`), so that the sandbox is left clean after each session.
34. As a DevOps engineer, I want the EC2 security group to allow inbound traffic only on ports 8000 (FastAPI), 3000 (Grafana), 9090 (Prometheus), and 5000 (MLflow) — and SSH from a restricted CIDR — so that the attack surface is minimised.
35. As a DevOps engineer, I want an Elastic IP attached to the EC2 instance, so that the service URL is stable across instance stops and starts.

### CI/CD Pipeline

36. As a developer, I want a `test` job that runs `pytest` on every push to `main` and every pull request, so that regressions are caught before merge.
37. As a developer, I want a `build-and-push` job that builds the FastAPI Docker image and pushes it to ECR on push to `main` and on version tags, so that every deployable artifact is stored in ECR.
38. As a developer, I want a `deploy` job that pulls the new image on the EC2 instance and restarts the service, running after `build-and-push`, so that a push to `main` results in the new version being live.
39. As a DevOps engineer, I want Pulumi infrastructure provisioned/updated as part of the deploy job using incremental update (`pulumi up`), so that infrastructure drift is corrected on every deploy without full teardown.
40. As a DevOps engineer, I want a Trivy security scan job in CI that fails on critical vulnerabilities, so that known CVEs are caught before deployment.
41. As a DevOps engineer, I want a `pulumi preview` job that runs on pull requests and comments the diff to the PR, so that infrastructure changes are reviewed before merge.
42. As a developer, I want all credentials (AWS keys, EC2 SSH key, ECR URL) stored in GitHub Secrets and never hardcoded, so that the repository can be public without leaking credentials.
43. As a developer, I want the deploy job to verify `/health` returns 200 after deployment, so that a broken deploy is caught immediately by CI.

### Engineering Documentation

44. As a teaching assistant, I want an `ARCHITECTURE.md` that fully describes the system without requiring me to read the code, so that I can evaluate the design decisions independently.
45. As a teaching assistant, I want at least five ADRs covering deployment topology, CI/CD strategy, data architecture, containerisation, and monitoring design, so that every major design choice is explained and justified.
46. As a teaching assistant, I want an architecture diagram showing every component, where it runs, the ports it uses, and how it communicates, so that the deployment topology is unambiguous.
47. As a new engineer, I want a runbook covering bootstrap from fresh clone, deploying a new model version, recovering from common failures, and full teardown, so that I can operate the system without prior knowledge.
48. As a teaching assistant, I want a "Known Limitations" section that honestly lists what the system does not handle, so that I can distinguish deliberate trade-offs from oversights.
49. As a developer, I want a `README.md` with setup instructions, endpoint table, environment variable table, and a GitHub Secrets list, so that anyone can get the stack running in under 15 minutes.

## Implementation Decisions

### ML Task
- Dataset: Kaggle `kartik2112/fraud-detection` (Credit Card Transactions Fraud Detection)
- Task: Binary classification — predict `is_fraud` (0 or 1)
- Algorithm: sklearn-compatible estimator (RandomForest, XGBoost, or LightGBM) with `class_weight='balanced'` to handle severe class imbalance (~0.5% fraud rate)
- Target baseline: ROC-AUC ≥ 0.85 on `fraudTest.csv`

### Feast Entity & Features
- Entity key: `cc_num` (credit card number, integer) — this is also the `entity_id` accepted by the API
- Feature view: transaction-level features aggregated or raw per `cc_num`
- Candidate features for online store: `amt`, `category` (encoded), `city_pop`, `lat`, `long`, `merch_lat`, `merch_long`, `hour_of_day`, `day_of_week`, `age` (derived from `dob`)
- Offline store: local Parquet file (`features.parquet`)
- Online store: Redis

### API Contract
- `POST /predict` accepts `{"entity_id": <int>}` where entity_id is a `cc_num`
- `GET /predict/<entity_id>?explain=true` returns prediction + feature values used
- `GET /rollback` switches the MLflow Production model to the previous registered version
- All errors return `{"error": "<message>", "detail": "<detail>"}` with appropriate HTTP status code

### Deployment Topology
- Option A: single AWS EC2 instance (`t3.small`) running all containers via Docker Compose
- Pulumi provisions: VPC, public subnet, security group, EC2 instance, Elastic IP, S3 bucket (MLflow artifacts + Feast offline), ECR repository (FastAPI image)
- MLflow artifact store: S3 in production, local volume in development
- Pulumi stack: incremental update (`pulumi up`) — not destroy-and-recreate

### CI/CD Structure
- `test` job: triggers on push to `main` and PRs; runs `pytest app/tests/`
- `build-and-push` job: triggers on push to `main` and version tags (`v*.*.*`); builds and pushes FastAPI image to ECR
- `deploy` job: triggers after `build-and-push`; SSHes into EC2, pulls new image, restarts Docker Compose, verifies `/health`
- `infra` job: runs `pulumi up` as part of deploy to keep infrastructure current
- `trivy-scan` job: scans Docker image for critical CVEs; fails the pipeline if found
- `pulumi-preview` job: runs on PRs only; comments Pulumi diff to the PR

### Infrastructure as Code
- Pulumi language: Python
- All resources tagged: `{"Project": "modelserve"}`
- ECR repository created with `force_delete=True` so `pulumi destroy` works even with images
- Stack outputs exported: EC2 public IP, ECR repository URL, S3 bucket name

### Observability
- Prometheus scrapes FastAPI `/metrics` on port 8000
- Grafana provisioned from `monitoring/grafana/provisioning/` — no manual UI setup required
- Dashboard panels: latency p50/p95/p99, request rate, error rate, model version gauge, Feast hit/miss ratio
- Alert rules: p95 latency > threshold, error rate > threshold, FastAPI service down

### Bonus Features (targeted)
- Trivy CI scan: +2 marks
- Pulumi PR preview comment: +2 marks
- `/rollback` endpoint: +2 marks
- Total bonus target: +6 marks

## Out of Scope

- Deep learning models (PyTorch, TensorFlow, Keras) — exam requires sklearn-compatible estimators only
- Model quality optimisation beyond a reasonable baseline (AUC ≥ 0.85) — infrastructure is the focus
- RDS, EKS, ALB, NAT Gateway, Lambda, SageMaker, or any managed AWS ML/container service
- Multi-node deployment (EKS, separate EC2 for each service)
- A/B traffic splitting between two models — excluded as too expensive for the bonus reward
- Blue/green deployment — excluded as too expensive for the bonus reward
- Custom Prometheus exporter for Feast stats — excluded in favour of higher-value items
- Real-time feature engineering (streaming) — offline materialisation is sufficient
- Model retraining pipeline — train.py is a one-shot script, not a scheduled pipeline
- Authentication or authorisation on the inference API
- HTTPS / TLS termination — plain HTTP on the EC2 instance is sufficient for this capstone

## Further Notes

- The Poridhi VM session structure is used as milestone naming only — the student works locally on macOS and is not constrained by 6-hour session time limits.
- The `data/` directory (containing `fraudTrain.csv` and `fraudTest.csv`) must be added to `.gitignore` — the CSV files are too large for git and should be downloaded from Kaggle once and stored locally.
- The `planing-and-sessions/` directory will contain `session-01.md` through `session-10.md` as checkpoint tracking files, each aligned to the exam's session milestone groupings.
- At the end of every real working session, `git push` is still the golden rule — even working locally, unpushed work is invisible to CI and the TA.
- The live demo requires a cold-start deployment in 10 minutes — the EC2 bootstrap (user-data script) must be fast and fully automated.
