all: build

# SETUP

setup-common:
	rm -rf .venv
	python3.14 -m venv .venv
	source .venv/bin/activate && pip install --upgrade pip && pip install -r requirements.txt

setup-settings:
	mkdir -p runtime
	cp settings-template.yaml runtime/settings.yaml
	brew install yq
	yq -i ".api_service_settings.jwt_settings.secret=\"$(shell openssl rand -hex 32)\"" runtime/settings.yaml

setup-dev: setup-common setup-settings
	yq -i ".env=\"ENVIRONMENT_DEV\"" runtime/settings.yaml
	make -C nginx setup-dev

setup-prod: setup-common setup-settings
	yq -i ".env=\"ENVIRONMENT_PROD\"" runtime/settings.yaml
	make -C nginx setup-prod

# BUILD

build-protos:
	make -C protos

build: build-protos
	make -C web
	make -C services

# RUN (dev)

run-python: build-protos
	PYTHONPATH=.:./protos python3

run-web:
	make -C web run

run-nginx:
	make -C nginx run
	
run-api: build-protos
	make -C services/api run

run-storage: build-protos
	make -C services/storage run

# DEPLOY (prod)
sync:
	git pull
	git submodule update --remote --recursive

deploy: sync build
	make -C services deploy