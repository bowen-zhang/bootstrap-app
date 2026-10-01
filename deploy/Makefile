include ../shared/common.mk

REPOS := web-bootstrap web api-service storage-service

AWS_ACCOUNT_ID := $(shell aws sts get-caller-identity --query Account --output text)
AWS_REGION := $(shell aws configure get region)
AWS_ECR_URI := $(AWS_ACCOUNT_ID).dkr.ecr.$(AWS_REGION).amazonaws.com
IMAGE_REGISTRY := $(AWS_ECR_URI)/$(APP_NAME)

ifndef AWS_ACCOUNT_ID
    $(error Missing AWS account id.)
endif
ifndef AWS_REGION
    $(error Missing AWS region.)
endif

.PHONY: build

login-aws:
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
	IMAGE_REGISTRY=$(IMAGE_REGISTRY)/ VERSION=$(VERSION) docker compose \
		--profile bootstrap \
		--profile staging \
		--profile prod \
		build

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

show-docker-commands:
	@echo export IMAGE_REGISTRY=$(IMAGE_REGISTRY)
	@echo export VERSION=$(VERSION)
	@echo docker-compose up -d web
	@echo docker-compose up -d api
	@echo docker-compose up -d storage

