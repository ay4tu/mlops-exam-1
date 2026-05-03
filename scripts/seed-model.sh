#!/bin/bash
# Train locally → register in EC2 MLflow → apply Feast registry → materialize into Redis
set -e
cd "$(dirname "$0")/.."

KEY="infrastructure/mlops-key"

echo "==> Getting EC2 IP from Pulumi"
IP=$(cd infrastructure && pulumi stack output instance_ip 2>/dev/null)
if [ -z "$IP" ]; then
  echo "ERROR: could not read instance_ip — run pulumi up first"
  exit 1
fi

if [ ! -f "data/fraudTrain.csv" ]; then
  echo "ERROR: data/fraudTrain.csv not found"
  exit 1
fi

echo "==> Training locally → registering in EC2 MLflow (http://$IP:5000)"
MLFLOW_TRACKING_URI="http://$IP:5000" \
GIT_PYTHON_REFRESH=quiet \
  python training/train.py

echo "==> Copying features.parquet to EC2"
scp -i "$KEY" -o StrictHostKeyChecking=no \
  training/features.parquet ec2-user@"$IP":/home/ec2-user/app/training/features.parquet

echo "==> Registering Feast feature views + materializing into Redis"
ssh -i "$KEY" -o StrictHostKeyChecking=no ec2-user@"$IP" \
  "docker exec app-fastapi-1 bash -c 'cd /app/feast_repo && feast apply' && \
   docker exec -e REDIS_HOST=redis app-fastapi-1 python /app/scripts/materialize_features.py"

echo ""
echo "Done — model registered, features in Redis."
echo "FastAPI will load the model within ~30 seconds (if not already up)."
