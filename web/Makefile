.PHONY: all run

all: build

setup:
	rm -rf node_modules
	npm install

build:
	npm run build

run:
	echo -ne "\e]0;web\a"
	npm run dev