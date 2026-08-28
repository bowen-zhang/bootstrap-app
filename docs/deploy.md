# Deployment

## First-Time Setup

### From Dev Machine

1. Copy docker compose file to EC2

    ```bash
    cd [PROJECT_DIR]
    scp docker-compose.yaml [host]:/home/ec2-user/[APP_NAME]/
    ```

### On EC2

1. Install Docker.

    ```bash
    sudo dnf install -y docker
    sudo systemctl start docker
    sudo systemctl enable docker
    sudo usermod -aG docker ec2-user
    newgrp docker
    ```

1. Install Docker Compose.

    ```bash
    sudo curl -SL "https://github.com/docker/compose/releases/latest/download/docker-compose-linux-$(uname -m)" \
        -o /usr/libexec/docker/cli-plugins/docker-compose
    sudo chmod +x /usr/libexec/docker/cli-plugins/docker-compose
    sudo curl -SL "https://github.com/docker/buildx/releases/download/v0.36.0/buildx-v0.36.0.linux-arm64" \
        -o /usr/libexec/docker/cli-plugins/docker-buildx
    sudo chmod +x /usr/libexec/docker/cli-plugins/docker-buildx

    ```

1. Login AWS.

    ```bash
    AWS_ACCOUNT_ID := $(aws sts get-caller-identity --query Account --output text)
    AWS_REGION := $(aws configure get region)
    aws ecr get-login-password --region $(AWS_REGION) | docker login --username AWS --password-stdin $(AWS_ACCOUNT_ID).dkr.ecr.$(AWS_REGION).amazonaws.com
    ```

1. Pull docker images

    ```bash
    cd [PROJECT_DIR]
    export IMAGE_REGISTRY=[AWS_ECR_URL]/
    export VERSION=[VERSION]
    docker compose --profile bootstrap --profile prod pull
    ```

1. Start a basic nginx server on port 80.

    ```bash    
    docker compose up web-bootstrap
    ```

1. Obtain SSL certificates
   
   ```bash
   docker compose run \
    --entrypoint "certbot certonly --webroot --webroot-path=/var/www/certbot -d yourdomain.com --email your@email.com --agree-tos" \
    certbot
    ```

1. Stop nginx server
1. Schedule nginx reload
   
    ```bash
    sudo dnf install -y cronie
    sudo systemctl enable --now crond
    sudo crontab -e
    ```

    Add the following:

    ```
    0 3 * * * /usr/bin/docker exec web nginx -s reload >> /var/log/nginx-cert-reload.log 2>&1
    ```

## Routine Rollout

1. Pull all docker images
1. Restart docker compose

    ```bash
    docker compose --profile prod down
    docker compose --profile prod up -d
    ```