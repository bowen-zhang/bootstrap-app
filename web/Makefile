.PHONY: all run

all: run

setup:
	rm -rf node_modules
	npm install

run:
	echo -ne "\e]0;web\a"
	npm run dev

build:
	npm run build