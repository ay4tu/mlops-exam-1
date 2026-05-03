#!/bin/bash
# One-time upload of training data to S3 (run once per fresh AWS session)
set -e
cd "$(dirname "$0")/.."

DATA_FILE="${DATA_FILE:-data/fraudTrain.csv}"

if [ ! -f "$DATA_FILE" ]; then
  echo "ERROR: $DATA_FILE not found — download the Kaggle dataset first"
  exit 1
fi

echo "==> Getting S3 bucket from Pulumi"
S3_BUCKET=$(cd infrastructure && pulumi stack output s3_bucket_name 2>/dev/null)
if [ -z "$S3_BUCKET" ]; then
  echo "ERROR: could not read s3_bucket_name — run pulumi up first"
  exit 1
fi

echo "==> Uploading $DATA_FILE to s3://$S3_BUCKET/data/fraudTrain.csv"
aws s3 cp "$DATA_FILE" "s3://$S3_BUCKET/data/fraudTrain.csv"
echo "Done: s3://$S3_BUCKET/data/fraudTrain.csv"
