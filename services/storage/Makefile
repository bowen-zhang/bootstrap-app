CURRENT_DIR := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))
ROOT_DIR = $(CURRENT_DIR)/../..

.PHONY: run

run:
	echo -ne "\e]0;Storage Service\a"
	. $(ROOT_DIR)/.venv/bin/activate && \
		PYTHONPATH=$(ROOT_DIR):$(ROOT_DIR)/protos python3 main.py
