from pathlib import Path
from protos import settings_pb
from third_party.bootstrap_utils import metric_utils, settings_utils


_DEFAULT_CONFIG_PATH = Path(__file__).parent.parent / "runtime" / "settings.yaml"


settings = settings_utils.SettingsLoader(settings_pb.Settings).load(_DEFAULT_CONFIG_PATH)

def is_dev():
    return settings.env == settings_pb.Environment.DEV

def is_prod():
    return settings.env == settings_pb.Environment.PROD

if is_prod():
    metric_builder = metric_utils.MetricBuilder(metric_utils.CloudWatchMetricWriter(settings.project_name))
else:
    metric_builder = metric_utils.MetricBuilder(metric_utils.ConsoleMetricWriter(settings.project_name))
