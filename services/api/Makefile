CURRENT_DIR := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))
ROOT_DIR = $(CURRENT_DIR)/../..

.PHONY: run

run:
	. $(ROOT_DIR)/.venv/bin/activate && PYTHONPATH=$(ROOT_DIR):$(ROOT_DIR)/protos DEV=1 python3 main.py
