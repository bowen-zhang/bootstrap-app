all: build

init-common:
	rm -rf .venv
	python3.14 -m venv .venv
	source .venv/bin/activate && pip install --upgrade pip && pip install -r requirements.txt

init-mac: init-common
	brew install yq

create-settings:
	mkdir -p runtime
	cp settings-template.yaml runtime/settings.yaml
	yq -i ".jwt_settings.secret=\"$(shell openssl rand -hex 32)\"" runtime/settings.yaml
	

build:
	make -C protos build
	make -C web build