include shared/common.mk

.PHONY: build

all: build

########################
# SETUP
#
# Mac:
#   - Install Homebrew: /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
#   - Install Docker Desktop: https://www.docker.com/products/docker-desktop/
#

setup-submodules:
	git submodule update --init --recursive

setup-mac:
	brew install awscli -y
	brew install protobuf -y
	brew install python@3.14 -y
	brew install node -y
	brew install nginx -y
	brew install yq -y
	brew install mkcert nss -y

setup-common:
	rm -rf .venv
	python3.14 -m venv .venv
	source .venv/bin/activate && \
		pip install --upgrade pip && \
		pip install -r requirements-dev.txt && \
		pip install -r requirements.txt

setup-settings:
	mkdir -p runtime
	if [ ! -e runtime/settings.yaml ]; then \
		cp settings-template.yaml runtime/settings.yaml && \
		yq -i ".api_service_settings.jwt_settings.secret=\"$$(openssl rand -hex 32)\"" runtime/settings.yaml; \
	fi
	if [ ! -e runtime/settings-prod.yaml ]; then \
		cp settings-template.yaml runtime/settings-prod.yaml && \
		yq -i ".env=\"ENVIRONMENT_PROD\" | .api_service_settings.jwt_settings.secret=\"$$(openssl rand -hex 32)\"" runtime/settings-prod.yaml; \
	fi

setup: setup-submodules setup-mac setup-common setup-settings
	yq -i ".env=\"ENVIRONMENT_DEV\"" runtime/settings.yaml
	make -C protos setup
	make -C nginx setup-dev
	make -C web setup

sync:
	git pull
	git submodule update --remote --recursive

# BUILD

build-protos:
	make -C protos

build: build-protos
	make -C web
	make -C nginx
	make -C deploy

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
