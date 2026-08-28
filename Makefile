APP_NAME := $(notdir $(CURDIR))
AWS_ACCOUNT_ID := $(shell aws sts get-caller-identity --query Account --output text)
AWS_REGION := $(shell aws configure get region)
AWS_ECR_URI := $(AWS_ACCOUNT_ID).dkr.ecr.$(AWS_REGION).amazonaws.com
IMAGE_REGISTRY := $(AWS_ECR_URI)/$(APP_NAME)
VERSION=$(shell git rev-parse --short HEAD)

all: build

test:
	echo $(FOLDER_NAME)

########################
# SETUP
#
# Mac:
#   - Install Homebrew: /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
#   - Install Docker Desktop: https://www.docker.com/products/docker-desktop/
#

prep-mac:
	brew install awscli -y
	brew install protobuf -y
	brew install python@3.14 -y
	brew install node -y
	brew install nginx -y
	brew install yq -y

setup-common:
	rm -rf .venv
	python3.14 -m venv .venv
	source .venv/bin/activate && \
		pip install --upgrade pip && \
		pip install -r requirements.txt

setup-settings:
	mkdir -p runtime
	cp settings-template.yaml runtime/settings.yaml
	yq -i ".api_service_settings.jwt_settings.secret=\"$(shell openssl rand -hex 32)\"" runtime/settings.yaml

setup: prep-mac setup-common setup-settings
	yq -i ".env=\"ENVIRONMENT_DEV\"" runtime/settings.yaml
	make -C protos setup
	make -C nginx setup-dev
	make -C web setup

login-aws:
	aws ecr get-login-password --region $(AWS_REGION) | docker login --username AWS --password-stdin $(AWS_ECR_URI)

# BUILD

build-protos:
	make -C protos

build: build-protos
	make -C web
	make -C nginx
	IMAGE_REGISTRY=$(IMAGE_REGISTRY)/ VERSION=$(VERSION) docker compose \
		--profile bootstrap \
		--profile staging \
		--profile prod \
		build

# RUN (dev)

run-python: build-protos
	PYTHONPATH=.:./protos python3

run-web:
	make -C web run

run-nginx:
	make -C nginx run
	
run-api:
	make -C services/api run

run-storage:
	make -C services/storage run

# DEPLOY (prod)
#   Set IMAGE_REGISTRY environment variable first.
deploy: build
	IMAGE_REGISTRY=$(IMAGE_REGISTRY)/ docker push $(IMAGE_REGISTRY)/web-bootstrap:$(VERSION)
	IMAGE_REGISTRY=$(IMAGE_REGISTRY)/ docker push $(IMAGE_REGISTRY)/web:$(VERSION)
	IMAGE_REGISTRY=$(IMAGE_REGISTRY)/ docker push $(IMAGE_REGISTRY)/api-service:$(VERSION)
	IMAGE_REGISTRY=$(IMAGE_REGISTRY)/ docker push $(IMAGE_REGISTRY)/storage-service:$(VERSION)
	@echo
	@echo "On AWS, run the following command:"
	@echo "  export IMAGE_REGISTRY=$(IMAGE_REGISTRY)/"
	@echo "  export VERSION=$(VERSION)"
	@echo "  aws ecr get-login-password --region $(AWS_REGION) | docker login \\"
	@echo "    --username AWS --password-stdin $(AWS_ACCOUNT_ID).dkr.ecr.$(AWS_REGION).amazonaws.com"
	@echo "  docker compose --profile bootstrap --profile prod pull"
	@echo
	@echo "For first time run:"
	@echo "  docker compose run \\"
	@echo "    --entrypoint \"certbot certonly --webroot --webroot-path=/var/www/certbot -d $(DOMAIN) --email $(ADMIN_EMAIL) --agree-tos\" \\"
	@echo "    certbot"
	@echo
	@echo "For subsequent runs:"
	@echo "  docker compose --profile prod"
	@echo


	
	
