include ../shared/common.mk

SETTINGS_FILE := $(RUNTIME_DIR)/config/settings.prod.yaml
ADMIN_EMAIL := $(shell yq '.admin_email' $(SETTINGS_FILE))
DOMAIN := $(shell yq '.domain' $(SETTINGS_FILE))

REPOS := web-bootstrap web api-service storage-service

AWS_ACCOUNT_ID := $(shell aws sts get-caller-identity --query Account --output text)
AWS_REGION := $(shell aws configure get region)
AWS_ECR_URI := $(AWS_ACCOUNT_ID).dkr.ecr.$(AWS_REGION).amazonaws.com
IMAGE_REGISTRY := $(AWS_ECR_URI)/$(APP_NAME)/

AWS_HOST ?= 

ifndef AWS_ACCOUNT_ID
    $(error Missing AWS account id.)
endif
ifndef AWS_REGION
    $(error Missing AWS region.)
endif

.PHONY: build

all: build

docker-login-aws:
	aws ecr get-login-password --region $(AWS_REGION) | docker login --username AWS --password-stdin $(AWS_ECR_URI)

create-aws-repos:
	for repo in $(REPOS); do \
		aws ecr create-repository \
			--repository-name $(APP_NAME)/$$repo \
			--image-scanning-configuration scanOnPush=true \
			--image-tag-mutability IMMUTABLE \
			--region $(AWS_REGION) \
			--no-cli-pager ; \
		aws ecr put-lifecycle-policy \
			--repository-name $(APP_NAME)/$$repo \
			--lifecycle-policy-text "file://$(abspath ecr_lifecycle_policy.json)" ; \
	done

build:
	IMAGE_REGISTRY=$(IMAGE_REGISTRY) VERSION=$(VERSION) docker compose \
		--profile bootstrap \
		--profile staging \
		--profile prod \
		build

# Staging Test

run-web-container:
	RUNTIME_DIR=$(RUNTIME_DIR) SETTINGS_FILE=settings.staging.yaml IMAGE_REGISTRY=$(IMAGE_REGISTRY) VERSION=$(VERSION) docker-compose up web-staging

run-api-container:
	RUNTIME_DIR=$(RUNTIME_DIR) SETTINGS_FILE=settings.staging.yaml IMAGE_REGISTRY=$(IMAGE_REGISTRY) VERSION=$(VERSION) docker-compose up api

run-storage-container:
	RUNTIME_DIR=$(RUNTIME_DIR) SETTINGS_FILE=settings.staging.yaml IMAGE_REGISTRY=$(IMAGE_REGISTRY) VERSION=$(VERSION) docker-compose up storage

run-atc-container:
	RUNTIME_DIR=$(RUNTIME_DIR) SETTINGS_FILE=settings.staging.yaml IMAGE_REGISTRY=$(IMAGE_REGISTRY) VERSION=$(VERSION) docker-compose up atc

# Prod deployment

upload: build docker-login-aws
	for repo in $(REPOS); do \
		IMAGE_REGISTRY=$(IMAGE_REGISTRY) docker push $(IMAGE_REGISTRY)$$repo:$(VERSION) ; \
	done

deploy:
	if [ -z "$(AWS_HOST)" ]; then \
		$(error Missing AWS host.) \
	fi

	echo "APP_NAME=$(APP_NAME)" > $(TMPDIR)/.env
	echo "IMAGE_REGISTRY=$(IMAGE_REGISTRY)" >> $(TMPDIR)/.env
	echo "VERSION=$(VERSION)" >> $(TMPDIR)/.env
	echo "AWS_REGION=$(AWS_REGION)" >> $(TMPDIR)/.env
	echo "AWS_ACCOUNT_ID=$(AWS_ACCOUNT_ID)" >> $(TMPDIR)/.env

	ssh $(AWS_HOST) "mkdir -p ~/${APP_NAME}/runtime/config"
	ssh $(AWS_HOST) "mkdir -p ~/${APP_NAME}/runtime/db"
	scp \
		$(TMPDIR)/.env \
		setup.sh reload.sh \
		docker-compose*.yaml \
		$(AWS_HOST):~/${APP_NAME}/
	scp \
		$(RUNTIME_DIR)/config/settings*.yaml \
		$(AWS_HOST):~/${APP_NAME}/runtime/config

	@echo
	@echo "On AWS, run the following command:"
	@echo "  For the first time, run:"
	@echo "    ./$(APP_NAME)/setup.sh"
	@echo
	@echo "  For subsequent runs:"
	@echo "    cd $(APP_NAME) && ./reload.sh"
	@echo
