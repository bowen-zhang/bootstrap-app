import os
from pathlib import Path

import yaml
from google.protobuf import json_format

from protos import settings_pb2

_DEFAULT_CONFIG_PATH = Path(__file__).parent.parent / "runtime" / "settings.yaml"

def _load(config_path: str | None = None) -> settings_pb2.Settings:
    settings_path = Path(config_path) if config_path is not None else _DEFAULT_CONFIG_PATH
    with settings_path.open("r", encoding="utf-8") as fh:
        parsed = yaml.safe_load(fh) or {}

    message = settings_pb2.Settings()
    json_format.ParseDict(parsed, message, ignore_unknown_fields=False)

    if os.environ.get("DEV", "") != "":
        message.env = settings_pb2.ENV_DEV

    return message


settings = _load()