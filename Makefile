all: build

init:
	rm -rf .venv
	python3.14 -m venv .venv
	source .venv/bin/activate && pip install --upgrade pip && pip install -r requirements.txt

build:
	make -C protos build
	make -C web build