include ../shared/common.mk

WORKING_DIR := $(PROJECT_DIR)/runtime/services


# Build a service file in runtime directory
# Inputs:
#   - Service Name (single word, no spaces)
#   - App Path
define build-service
	mkdir -p $(WORKING_DIR)
	cp $(PROJECT_DIR)/services/template.service $(WORKING_DIR)/$(1).service
	sed $(SED_FLAGS) 's|{ROOT_DIR}|$(PROJECT_DIR)|g' $(WORKING_DIR)/$(1).service
	sed $(SED_FLAGS) 's|{SERVICE_NAME}|$(1)|g' $(WORKING_DIR)/$(1).service
	sed $(SED_FLAGS) 's|{APP_PATH}|$(2)|g' $(WORKING_DIR)/$(1).service
	rm -f $(WORKING_DIR)/*.service.bak
endef

# Deploy a service file to systemd
# Inputs:
#   - Service Name (single word, no spaces)
define deploy-service
	sudo systemctl stop $(1).service
	sudo cp $(WORKING_DIR)/$(1).service /etc/systemd/system/
	sudo systemctl daemon-reload
	sudo systemctl enable $(1).service
	sudo systemctl start $(1).service
endef

build:
	$(call build-service,api,services/api/main.py)
	$(call build-service,storage,services/storage/main.py)

deploy:
	$(call deploy-service,api)
	$(call deploy-service,storage)
