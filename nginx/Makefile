CURRENT_DIR := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))
PROJECT_DIR := $(CURRENT_DIR)..
RUNTIME_DIR := $(PROJECT_DIR)/runtime
WORKING_DIR := $(RUNTIME_DIR)/nginx
SETTINGS_FILE := $(RUNTIME_DIR)/settings.yaml
CONF := $(WORKING_DIR)/nginx-dev.conf
LOG_DIR := $(WORKING_DIR)/logs
ERR_LOG := $(LOG_DIR)/error.log
ADMIN_EMAIL := $(shell yq '.admin_email' $(SETTINGS_FILE))
DOMAIN := $(shell yq '.domain' $(SETTINGS_FILE))

.PHONY: all run

all: run-dev

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

# Setup EC2 instance with nginx, certbot, and SSL certificate
setup-prod: setup
	sudo dnf install nginx certbot python3-certbot-nginx -y
	sudo systemctl stop nginx

	sudo cp $(CURRENT_DIR)/nginx-prod.conf /etc/nginx/nginx.conf
	sudo sed -i '' "s|\[PROJECT_DIR\]|$(PROJECT_DIR)|g" /tmp/nginx.conf

	sudo certbot --non-interactive --agree-tos -m $(ADMIN_EMAIL) --nginx -d $(DOMAIN) -d www.$(DOMAIN)
	sudo systemctl enable --now certbot-renew.timer

	sudo systemctl enable nginx
	sudo systemctl start nginx

# RUN (dev)
run:
	cp $(CURRENT_DIR)/nginx-dev.conf $(CONF)
	exec nginx -p $(WORKING_DIR) -e $(ERR_LOG) -c $(CONF) -g 'daemon off;'
