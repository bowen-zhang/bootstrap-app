CURRENT_DIR := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))
PROJECT_DIR := $(abspath $(CURRENT_DIR)..)
RUNTIME_DIR := $(PROJECT_DIR)/runtime
SETTINGS_FILE := $(RUNTIME_DIR)/settings.yaml
ENV := $(shell yq '.env' $(SETTINGS_FILE))
ADMIN_EMAIL := $(shell yq '.admin_email' $(SETTINGS_FILE))
DOMAIN := $(shell yq '.domain' $(SETTINGS_FILE))

OS := $(shell uname -s)
ifeq ($(OS),Darwin)
    SED_FLAGS="-i.bak"
else
    SED_FLAGS="-i"
endif

ifeq ($(ENV),ENVIRONMENT_DEV)
	IS_DEV := true
	IS_PROD := false
else ifeq ($(ENV),ENVIRONMENT_PROD)
	IS_DEV := false
	IS_PROD := true
else
	$(error "Unknown environment: $(ENV)")
endif