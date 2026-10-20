#!/bin/bash

set -o allexport
source .env
set +o allexport

sudo yum update -y

# Install Docker
sudo yum install -y docker
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker $USER
newgrp docker

# Install Docker Compose
sudo mkdir -p /usr/libexec/docker/cli-plugins/
sudo curl -SL "https://github.com/docker/compose/releases/latest/download/docker-compose-linux-$(uname -m)" -o /usr/libexec/docker/cli-plugins/docker-compose
sudo chmod +x /usr/libexec/docker/cli-plugins/docker-compose
sudo systemctl restart docker
docker compose version

# Install AWS Cli
curl "https://awscli.amazonaws.com/awscli-exe-linux-aarch64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install
rm awscliv2.zip
rm -rf aws
aws --version

# Bootstrap

aws login --remote
aws ecr get-login-password --region ${AWS_REGION} | \
    docker login --username AWS --password-stdin ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com
docker compose -f docker-compose.yaml -f docker-compose.prod.yaml --profile bootstrap --profile prod pull

docker compose up -d web-bootstrap
docker compose -f docker-compose.yaml -f docker-compose.prod.yaml run \
	--entrypoint "certbot certonly --webroot --webroot-path=/var/www/certbot -d ${DOMAIN} -d www.${DOMAIN} --email ${ADMIN_EMAIL} --agree-tos --no-eff-email" \
	certbot
docker compose down web-bootstrap