#!/bin/bash
# Full deploy: build image, push to ECR, restart stack on EC2
set -e
cd "$(dirname "$0")/.."

TAG=${1:-latest}
COMPOSE_FILE="docker-compose.prod.yml"
KEY="infrastructure/mlops-key"

echo "==> [1/4] Build & push image to ECR"
./scripts/push-to-ecr.sh "$TAG"

echo "==> [2/4] Get EC2 IP from Pulumi"
IP=$(cd infrastructure && pulumi stack output instance_ip 2>/dev/null)
if [ -z "$IP" ]; then
  echo "ERROR: could not read instance_ip — run pulumi up first"
  exit 1
fi
echo "     EC2: $IP"

echo "==> [3/4] Restart stack on EC2"
ssh -i "$KEY" -o StrictHostKeyChecking=no ec2-user@"$IP" bash <<'REMOTE'
  set -e
  cd /home/ec2-user/app
  git pull --ff-only
  ECR_URL=$(aws ecr describe-repositories \
    --query 'repositories[0].repositoryUri' \
    --output text --region ap-southeast-1)
  aws ecr get-login-password --region ap-southeast-1 | \
    docker login --username AWS --password-stdin "$ECR_URL"
  docker-compose -f docker-compose.yml -f docker-compose.prod.yml pull
  docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --remove-orphans
  echo "Stack restarted."
REMOTE

echo "==> [4/4] Register model + materialize features"
./scripts/train-on-ec2.sh

echo ""
echo "Done. Endpoints:"
echo "  http://$IP:8000/health"
echo "  http://$IP:8000/predict"
echo "  http://$IP:5000  (MLflow)"
echo "  http://$IP:3000  (Grafana)"
echo "  http://$IP:9090  (Prometheus)"
