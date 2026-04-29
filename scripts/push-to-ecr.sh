#!/bin/bash
set -e
cd "$(dirname "$0")/.."

TAG=${1:-latest}
ECR_URL=$(cd infrastructure && pulumi stack output ecr_repository_url 2>/dev/null)
REGION=$(cd infrastructure && pulumi config get aws:region 2>/dev/null || echo "ap-southeast-1")

if [ -z "$ECR_URL" ]; then
  echo "ERROR: could not read ecr_repository_url — run pulumi up first"
  exit 1
fi

echo "Logging into ECR..."
aws ecr get-login-password --region "$REGION" | \
  docker login --username AWS --password-stdin "$ECR_URL"

echo "Building image..."
docker build -t "$ECR_URL:$TAG" .

echo "Pushing $ECR_URL:$TAG ..."
docker push "$ECR_URL:$TAG"

echo "Done: $ECR_URL:$TAG"
