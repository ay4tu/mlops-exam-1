#!/bin/bash
# SSH into EC2, download training data from S3, run train.py + feast materialize
set -e
cd "$(dirname "$0")/.."

KEY="infrastructure/mlops-key"

echo "==> Getting EC2 IP from Pulumi"
IP=$(cd infrastructure && pulumi stack output instance_ip 2>/dev/null)
if [ -z "$IP" ]; then
  echo "ERROR: could not read instance_ip — run pulumi up first"
  exit 1
fi
echo "     EC2: $IP"

ssh -i "$KEY" -o StrictHostKeyChecking=no ec2-user@"$IP" bash <<'REMOTE'
set -e
cd /home/ec2-user/app

S3_BUCKET=$(grep MLFLOW_S3_BUCKET .env | cut -d= -f2)
ECR_URL=$(aws ecr describe-repositories \
  --query 'repositories[0].repositoryUri' \
  --output text --region ap-southeast-1)

echo "==> Downloading training data from s3://$S3_BUCKET/data/fraudTrain.csv"
mkdir -p data
aws s3 cp "s3://$S3_BUCKET/data/fraudTrain.csv" data/fraudTrain.csv

echo "==> Running train.py"
docker run --rm \
  --network app_default \
  -v /home/ec2-user/app/data:/app/data \
  -v /home/ec2-user/app/training:/app/training \
  -e MLFLOW_TRACKING_URI=http://mlflow:5000 \
  "$ECR_URL:latest" \
  python training/train.py
echo "Training done."

echo "==> Running feast materialize"
docker run --rm \
  --network app_default \
  -v /home/ec2-user/app/feast_repo:/app/feast_repo \
  -v /home/ec2-user/app/training:/app/training \
  -e REDIS_HOST=redis \
  "$ECR_URL:latest" \
  bash -c "cd /app/feast_repo && feast materialize-incremental \$(date -u +%Y-%m-%dT%H:%M:%S)"
echo "Feast done."
REMOTE

echo "Done — model registered, features materialized."
echo "FastAPI will load the model within ~30 seconds."
