#!/bin/bash

set -o allexport
source .env
set +o allexport

if aws sts get-caller-identity &>/dev/null; then
    echo "Active session found. Skipping login."
else
    aws login --remote
fi
aws ecr get-login-password --region ${AWS_REGION} | \
    docker login --username AWS --password-stdin ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com
docker compose -f docker-compose.yaml -f docker-compose.prod.yaml --profile bootstrap --profile prod pull

docker compose -f docker-compose.yaml -f docker-compose.prod.yaml --profile prod up -d