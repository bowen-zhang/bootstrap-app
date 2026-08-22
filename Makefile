all: build

init-common:
	rm -rf .venv
	python3.14 -m venv .venv
	source .venv/bin/activate && pip install --upgrade pip && pip install -r requirements.txt

init-mac: init-common
	brew install yq

create-dev-settings: create-settings-common
	yq -i ".env=\"ENVIRONMENT_DEV\"" runtime/settings.yaml

create-prod-settings: create-settings-common
	yq -i ".env=\"ENVIRONMENT_PROD\"" runtime/settings.yaml

create-settings-common:
	mkdir -p runtime
	cp settings-template.yaml runtime/settings.yaml
	yq -i ".api_service_settings.jwt_settings.secret=\"$(shell openssl rand -hex 32)\"" runtime/settings.yaml

build:
	make -C protos build
	make -C web build

run-python:
	PYTHONPATH=.:./protos python3