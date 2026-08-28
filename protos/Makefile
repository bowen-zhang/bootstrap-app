include ../shared/common.mk

PROTO_DIR := .
PROTO_FILES := $(PROTO_DIR)/*.proto

PY_OUT := .
JS_OUT := ../web/src/libs

ifeq ($(IS_DEV),true)
	PYI_OUT := --pyi_out=$(PY_OUT)
else
	PYI_OUT :=
endif

.PHONY: build python connect-js clean

build: clean python connect-js

setup:
	npm install

python:
	source ../.venv/bin/activate && protoc \
		-I $(PROTO_DIR) \
		--py_out=$(PY_OUT) \
		$(PYI_OUT) \
		--connectrpc_out=$(PY_OUT) \
		$(PROTO_FILES)

connect-js:
	NODE_OPTIONS="--no-warnings" npx protoc \
		-I $(PROTO_DIR) \
		--es_out=$(JS_OUT) \
		--es_opt=target=ts \
		$(PROTO_FILES)

clean:
	mkdir -p $(PY_OUT)
	rm -rf $(PY_OUT)/*_pb*.py*
	rm -rf $(PY_OUT)/*_connect.py
	mkdir -p $(JS_OUT)
	rm -rf $(JS_OUT)/*_pb.ts
	rm -rf $(JS_OUT)/*_connect.ts
