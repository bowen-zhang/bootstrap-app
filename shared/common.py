import os
from pathlib import Path
from protos import settings_pb
from third_party.bootstrap_utils import metric_utils, settings_utils


_DEFAULT_SETTINGS_FILE = os.getenv("SETTINGS_FILE", "settings.yaml")
_DEFAULT_SETTINGS_PATH = Path(__file__).parent.parent / "runtime" / _DEFAULT_SETTINGS_FILE

settings = settings_utils.SettingsLoader(settings_pb.Settings).load(_DEFAULT_SETTINGS_PATH)

def is_dev():
    return settings.env == settings_pb.Environment.DEV

def is_prod():
    return settings.env == settings_pb.Environment.PROD

match settings.observability:
    case settings_pb.Observability.AWS:
        metric_builder = metric_utils.MetricBuilder(metric_utils.CloudWatchMetricWriter(settings.project_name))
    case settings_pb.Observability.LOCAL:
        metric_builder = metric_utils.MetricBuilder(metric_utils.ConsoleMetricWriter(settings.project_name))
    case _:
        raise ValueError(f"Unsupported observability setting: {settings.observability}")
