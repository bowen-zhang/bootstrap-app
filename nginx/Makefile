.PHONY: all run

CURRENT_DIR := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))
NGINX ?= nginx
CONF ?= nginx-dev.conf
LOG_DIR ?= logs
ERR_LOG ?= $(LOG_DIR)/error.log

all: run-dev

run-dev:
	mkdir -p $(LOG_DIR)
	exec $(NGINX) -p $(CURRENT_DIR) -e $(ERR_LOG) -c $(CONF) -g 'daemon off;'

create-localhost-cert:
	brew install mkcert nss
	mkcert -install
	mkcert localhost 127.0.0.1 ::1

run-prod:
	mkdir -p $(LOG_DIR)
	exec $(NGINX) -p $(CURRENT_DIR) -e $(ERR_LOG) -c nginx-prod.conf -g 'daemon off;'