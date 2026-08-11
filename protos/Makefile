PROTO_DIR := .
PROTO_FILES := $(PROTO_DIR)/*.proto

PY_OUT := .
JS_OUT := ../web/src/libs

.PHONY: build python connect-js clean

build: clean python connect-js

setup:
	npm install

python:
	protoc \
		-I $(PROTO_DIR) \
		--python_out=$(PY_OUT) \
		--pyi_out=$(PY_OUT) \
		--connectrpc_out=protobuf=google:$(PY_OUT) \
		$(PROTO_FILES)

connect-js:
	protoc \
		-I $(PROTO_DIR) \
		--es_out=$(JS_OUT) \
		--es_opt=target=ts \
		$(PROTO_FILES)

clean:
	mkdir -p $(PY_OUT)
	rm -rf $(PY_OUT)/*_pb*.py
	rm -rf $(PY_OUT)/*_connect.py
	mkdir -p $(JS_OUT)
	rm -rf $(JS_OUT)/*_pb.ts
