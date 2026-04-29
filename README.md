# ModelServe

> MLOps with Cloud Season 2 — Capstone Exam

A fraud-detection inference service built with FastAPI, MLflow, Feast, and Prometheus. Trains a gradient-boosting model on credit card transaction data, serves online predictions keyed by `cc_num`, and exposes Prometheus metrics — all wired together with Docker Compose and deployed to AWS EC2 via GitHub Actions.

## Prerequisites

- Docker Desktop (with Compose v2)
- Python 3.11+ with `venv`
- `fraudTrain.csv` downloaded from Kaggle (see Dataset section below)
- macOS / Linux (Windows works via WSL2)

> **macOS note:** Port 5000 is taken by AirPlay Receiver. MLflow is exposed on **5001** in this setup.

## Quick Start (Local Development — Session 01)

### 1. Clone and create virtual environment

```bash
git clone <repo-url>
cd mlops-exam-1
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Download the dataset

Download `fraudTrain.csv` from [Kaggle](https://www.kaggle.com/datasets/kartik2112/fraud-detection) and place it in `data/`:

```
data/
└── fraudTrain.csv   (~335 MB, gitignored)
```

### 3. Configure environment

```bash
cp .env.example .env
# Edit .env if you need different credentials (defaults work out of the box)
```

### 4. Start Postgres + MLflow

```bash
docker compose up postgres mlflow -d
```

Wait ~20 seconds, then verify:

```bash
curl http://localhost:5001/health   # should return: OK
```

### 5. Train the model

```bash
MLFLOW_TRACKING_URI=http://localhost:5001 python training/train.py
```

This takes ~30 seconds. When finished:
- MLflow UI at **http://localhost:5001** shows the `fraud-detection` experiment
- `fraud-detector` model is registered and promoted to **Production**
- `training/features.parquet` and `training/sample_request.json` are written to disk

### 6. Verify

```bash
ls -lh training/features.parquet training/sample_request.json
cat training/sample_request.json
open http://localhost:5001          # MLflow UI
```

---

> **Sessions 2–6** add Redis, FastAPI inference service, Prometheus/Grafana, Pulumi AWS infra, and GitHub Actions CI/CD. See `plans/modelserve-plan.md` for the full roadmap.

---

## AWS Infrastructure (Session 05)

Provisions a complete AWS environment via Pulumi: VPC, public subnet, Internet Gateway, security group, EC2 (`t3.medium`), Elastic IP, S3 bucket, and ECR repository — all tagged `Project: modelserve`.

### Prerequisites

- [Pulumi CLI](https://www.pulumi.com/docs/install/) installed
- AWS credentials configured (`aws configure` or environment variables)
- Python 3.11+ with `venv`

### Deploy

```bash
# 1. Generate SSH key (once)
ssh-keygen -t rsa -b 4096 -f infrastructure/mlops-key -N ""
export SSH_PUBLIC_KEY="$(cat infrastructure/mlops-key.pub)"

# 2. Install Pulumi dependencies
cd infrastructure
python3 -m venv venv
venv/bin/pip install -r requirements.txt

# 3. Configure stack
pulumi stack init dev
pulumi config set aws:region ap-southeast-1   # or your region

# 4. Deploy
pulumi up --yes
```

### SSH into EC2

```bash
ssh -i infrastructure/mlops-key ec2-user@$(cd infrastructure && pulumi stack output instance_ip)
```

### Stack outputs

| Output | Description |
|--------|-------------|
| `instance_ip` | Elastic IP of the EC2 instance |
| `ecr_repository_url` | ECR repository URL for Docker image pushes |
| `s3_bucket_name` | S3 bucket for MLflow artifacts and Feast offline store |

### Tear down

```bash
cd infrastructure && pulumi destroy --yes
```

---

## REST Endpoints

| Method | Path | Description | Example response |
|--------|------|-------------|-----------------|
| GET | `/health` | Liveness check | `{"status":"healthy","model_version":"2"}` |
| POST | `/predict` | Predict fraud from body JSON | `{"prediction":0,"probability":0.02,"model_version":"2","timestamp":"..."}` |
| GET | `/predict/<entity_id>?explain=true` | Predict + return feature values | adds `"features":{...}` to response |
| GET | `/metrics` | Prometheus text format metrics | `prediction_requests_total{...}` |
| GET | `/rollback` | Roll active model back to previous Production version | `{"active_version":"1"}` |

## Environment Variables

Copy `.env.example` to `.env` and fill in the values:

| Variable | Description | Default |
|----------|-------------|---------|
| `POSTGRES_USER` | PostgreSQL username (MLflow backend) | `mlflow` |
| `POSTGRES_PASSWORD` | PostgreSQL password | `mlflow` |
| `POSTGRES_DB` | PostgreSQL database name | `mlflow` |
| `MLFLOW_TRACKING_URI` | MLflow server URL (from host machine) | `http://localhost:5001` |
| `MLFLOW_BACKEND_STORE_URI` | Full Postgres URI (used in production) | see `.env.example` |
| `REDIS_HOST` | Redis host for Feast online store | `localhost` |
| `REDIS_PORT` | Redis port | `6379` |
| `MODEL_NAME` | Registered model name in MLflow | `fraud-detector` |
| `MODEL_STAGE` | Model stage to load | `Production` |
| `AWS_ACCESS_KEY_ID` | AWS credentials (production only) | — |
| `AWS_SECRET_ACCESS_KEY` | AWS credentials (production only) | — |
| `AWS_REGION` | AWS region | `us-east-1` |

## GitHub Secrets

| Secret | Purpose |
|--------|---------|
| `AWS_ACCESS_KEY_ID` | Authenticate with AWS for ECR push and EC2 deploy |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key |
| `AWS_REGION` | AWS region for all resources |
| `EC2_HOST` | Public IP of the EC2 instance |
| `EC2_SSH_KEY` | Private SSH key for EC2 access |
| `ECR_REPOSITORY` | ECR repository URL for Docker image pushes |

## Engineering Documentation

See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for architecture overview, ADRs, CI/CD runbook, and known limitations.

## Dataset

[Credit Card Transactions Fraud Detection](https://www.kaggle.com/datasets/kartik2112/fraud-detection) — Simulated credit card transactions generated using Sparkov. Use `fraudTrain.csv` (~1.3M rows, 22 features). Entity key: `cc_num`. File is gitignored — download manually to `data/`.

---

*MLOps with Cloud Season 2 — Capstone: ModelServe | Poridhi.io*
