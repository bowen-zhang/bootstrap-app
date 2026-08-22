import json
import os
import yaml

from pathlib import Path

from protos import settings_pb


_DEFAULT_CONFIG_PATH = Path(__file__).parent.parent / "runtime" / "settings.yaml"

def _load(config_path: str | None = None) -> settings_pb.Settings:
    settings_path = Path(config_path) if config_path is not None else _DEFAULT_CONFIG_PATH
    with settings_path.open("r", encoding="utf-8") as fh:
        parsed = yaml.safe_load(fh) or {}

    message = settings_pb.Settings.from_json(json.dumps(parsed))
   
    if os.environ.get("DEV", "") != "":
        message.env = settings_pb.Environment.DEV

    return message


settings = _load()

def is_dev():
    return settings.env == settings_pb.Environment.DEV