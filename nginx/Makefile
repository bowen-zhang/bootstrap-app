include ../shared/common.mk

PROD_SETTINGS_FILE := $(RUNTIME_DIR)/settings-prod.yaml
WORKING_DIR := $(RUNTIME_DIR)/nginx
LOG_DIR := $(WORKING_DIR)/logs
ERR_LOG := $(LOG_DIR)/error.log
DOMAIN := $(shell yq '.domain' $(PROD_SETTINGS_FILE))
API_HOSTNAME := $(shell yq '.api_service_settings.hostname' $(PROD_SETTINGS_FILE))
API_PORT := $(shell yq '.api_service_settings.port' $(PROD_SETTINGS_FILE))

.PHONY: all run

all: build

# SETUP

setup:
	mkdir -p $(LOG_DIR)
	mkdir -p $(WORKING_DIR)

setup-dev: setup
	cp $(CURRENT_DIR)/mime.types $(WORKING_DIR)
	brew install mkcert nss -y
	cd $(WORKING_DIR) && \
		mkcert -install && \
		mkcert localhost 127.0.0.1 ::1

# BUILD

clear:
	rm -rf $(WORKING_DIR)/nginx*.conf

build: clear
	@cp nginx*.conf $(WORKING_DIR)

	@echo "Building nginx-bootstrap.conf"
	@sed -i.bak "s|\[DOMAIN\]|$(DOMAIN)|g" $(WORKING_DIR)/nginx-bootstrap.conf

	@echo "Building nginx-staging.conf"
	@sed -i.bak "s|\[API_HOSTNAME\]|$(API_HOSTNAME)|g" $(WORKING_DIR)/nginx-staging.conf
	@sed -i.bak "s|\[API_PORT\]|$(API_PORT)|g" $(WORKING_DIR)/nginx-staging.conf

	@echo "Building nginx-prod.conf"
	@sed -i.bak "s|\[DOMAIN\]|$(DOMAIN)|g" $(WORKING_DIR)/nginx-prod.conf	
	@sed -i.bak "s|\[API_HOSTNAME\]|$(API_HOSTNAME)|g" $(WORKING_DIR)/nginx-prod.conf
	@sed -i.bak "s|\[API_PORT\]|$(API_PORT)|g" $(WORKING_DIR)/nginx-prod.conf

	@rm -f $(WORKING_DIR)/*.bak

# RUN (dev)

run: build
	exec nginx -p $(WORKING_DIR) -e $(ERR_LOG) -c $(WORKING_DIR)/nginx-dev.conf -g 'daemon off;'
