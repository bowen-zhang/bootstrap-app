#!/bin/bash

ROOT_DIR="$( cd "$( dirname "$0" )/.." &> /dev/null && pwd )"

PYTHON=python3
PYTHONPATH=$ROOT_DIR:$ROOT_DIR/protos
PYTHONUNBUFFERED=1

APP=${1}

echo "Root directory: $ROOT_DIR"
cd $ROOT_DIR

echo "Activating virtual environment..."
source .venv/bin/activate

echo "Starting report service..."
PYTHONPATH=$PYTHONPATH $PYTHON $APP