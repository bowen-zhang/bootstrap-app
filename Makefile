all: build

########################
# SETUP
#
# Mac: Install Homebrew first:
#   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
# EC2: Install git & npm first
#   sudo dnf install git make -y
#   curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
#   source ~/.bashrc
#   nvm install --lts

prep-mac:
	brew install protobuf -y
	brew install python@3.14 -y
	brew install node -y
	brew install nginx -y
	brew install yq -y

prep-ec2:
	sudo dnf install -y protobuf-devel python3.14 nginx yq

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

setup-dev: prep-mac setup-common setup-settings
	yq -i ".env=\"ENVIRONMENT_DEV\"" runtime/settings.yaml
	make -C protos setup
	make -C nginx setup-dev
	make -C web setup

setup-prod: prep-ec2 setup-common setup-settings
	yq -i ".env=\"ENVIRONMENT_PROD\"" runtime/settings.yaml
	make -C protos setup
	make -C nginx setup-prod
	make -C web setup

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
	
run-api:
	make -C services/api run

run-storage:
	make -C services/storage run

# DEPLOY (prod)
sync:
	git pull
	git submodule update --remote --recursive

deploy: sync build
	make -C services deploy