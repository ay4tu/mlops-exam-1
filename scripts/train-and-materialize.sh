#!/bin/bash
# Called by Pulumi local.Command after a new EC2 instance is provisioned.
# Trains fraud-detector → registers in MLflow → materializes features into Redis
# → starts the full docker-compose stack on EC2.
#
# Required env vars (injected by Pulumi):
#   EC2_IP      public IP of the EC2 instance
#   ECR_URL     full ECR repository URL (no tag)
#   SSH_KEY     path to the SSH private key
#   AWS_REGION  AWS region
set -e
cd "$(dirname "$0")/.."

# When run manually, populate vars from pulumi stack output
if [ -z "$EC2_IP" ]; then
  EC2_IP=$(cd infrastructure && pulumi stack output instance_ip 2>/dev/null)
fi
if [ -z "$ECR_URL" ]; then
  ECR_URL=$(cd infrastructure && pulumi stack output ecr_repository_url 2>/dev/null)
fi
if [ -z "$SSH_KEY" ]; then
  SSH_KEY="infrastructure/mlops-key"
fi
if [ -z "$AWS_REGION" ]; then
  AWS_REGION=$(cd infrastructure && pulumi config get aws:region 2>/dev/null || echo "ap-southeast-1")
fi

[ -z "$EC2_IP" ] && { echo "ERROR: EC2_IP not set and pulumi stack output failed"; exit 1; }

SSH_OPTS="-i $SSH_KEY -o StrictHostKeyChecking=no -o ConnectTimeout=10"

# ── Wait for SSH ──────────────────────────────────────────────────────────────
echo "[bootstrap] Waiting for SSH on $EC2_IP..."
for i in $(seq 1 30); do
  ssh $SSH_OPTS ec2-user@$EC2_IP "echo ok" 2>/dev/null && break
  echo "  attempt $i/30 ..."
  sleep 10
done
ssh $SSH_OPTS ec2-user@$EC2_IP "echo ok" >/dev/null || { echo "ERROR: SSH unreachable after 5 min"; exit 1; }

# ── Wait for MLflow ───────────────────────────────────────────────────────────
echo "[bootstrap] Waiting for MLflow at http://$EC2_IP:5000 ..."
for i in $(seq 1 60); do
  curl -sf "http://$EC2_IP:5000/health" >/dev/null 2>&1 && break
  echo "  attempt $i/60 ..."
  sleep 10
done
curl -sf "http://$EC2_IP:5000/health" >/dev/null || { echo "ERROR: MLflow not healthy after 10 min"; exit 1; }
echo "[bootstrap] MLflow is up."

# ── Train ─────────────────────────────────────────────────────────────────────
echo "[bootstrap] Training model (this takes ~5 min)..."
MLFLOW_TRACKING_URI="http://$EC2_IP:5000" .venv/bin/python training/train.py

# ── Copy features.parquet to EC2 ─────────────────────────────────────────────
echo "[bootstrap] Copying features.parquet to EC2..."
ssh $SSH_OPTS ec2-user@$EC2_IP "mkdir -p /home/ec2-user/app/training"
scp -i "$SSH_KEY" -o StrictHostKeyChecking=no \
  training/features.parquet \
  ec2-user@$EC2_IP:/home/ec2-user/app/training/features.parquet

# ── Materialize features into Redis ──────────────────────────────────────────
echo "[bootstrap] Materializing Feast features into Redis..."
ssh $SSH_OPTS ec2-user@$EC2_IP "
  set -e
  aws ecr get-login-password --region $AWS_REGION | \
    docker login --username AWS --password-stdin \$(echo $ECR_URL | cut -d/ -f1) 2>/dev/null
  docker run --rm \
    --network app_default \
    -v /home/ec2-user/app/feast_repo:/app/feast_repo \
    -v /home/ec2-user/app/training:/app/training \
    -v /home/ec2-user/app/scripts:/app/scripts \
    -e REDIS_HOST=redis \
    -e REDIS_PORT=6379 \
    $ECR_URL:latest \
    bash -c 'cd /app/feast_repo && feast apply && cd /app && python scripts/materialize_features.py'
"

# ── Start full stack ──────────────────────────────────────────────────────────
echo "[bootstrap] Starting full stack (FastAPI + Prometheus + Grafana)..."
ssh $SSH_OPTS ec2-user@$EC2_IP "
  cd /home/ec2-user/app
  docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
"

echo "[bootstrap] Done — stack live at http://$EC2_IP:8000"
