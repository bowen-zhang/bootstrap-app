CURRENT_DIR := $(patsubst %/,%,$(dir $(abspath $(lastword $(MAKEFILE_LIST)))))
PROJECT_DIR := $(patsubst %/,%,$(dir $(CURRENT_DIR)))
RUNTIME_DIR := $(PROJECT_DIR)/runtime

APP_NAME := $(notdir $(PROJECT_DIR))
VERSION=$(shell git rev-parse --short HEAD)

ifeq ($(OS),Windows_NT)
    DETECTED_OS := Windows
else
	UNAME_S := $(shell uname -s)
    ifeq ($(UNAME_S),Darwin)
        DETECTED_OS := MacOS
    endif
    ifeq ($(UNAME_S),Linux)
        DETECTED_OS := Linux
    endif
endif

ifeq ($(DETECTED_OS), Windows)
	ACTIVATE_VENV := $(PROJECT_DIR)/.venv/Scripts/activate.bat
	PATH_SEPARATOR := \;
	NATIVE_SHELL := cmd.exe //c
else ifeq ($(DETECTED_OS), MacOS)
	ACTIVATE_VENV := source $(PROJECT_DIR)/.venv/bin/activate
    SED_FLAGS="-i.bak"
	PATH_SEPARATOR := :
else ifeq ($(DETECTED_OS), Linux)
	ACTIVATE_VENV := source $(PROJECT_DIR)/.venv/bin/activate
    SED_FLAGS="-i"
	PATH_SEPARATOR := :
endif
