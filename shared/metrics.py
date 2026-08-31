import boto3
import logging
import time

from abc import ABC, abstractmethod

from shared.settings import is_prod, settings


_logger = logging.getLogger(__name__)

class MockCloudWatchClient:
    """No-Op client for local development to avoid AWS CloudWatch calls."""
    def put_metric_data(self, Namespace, MetricData):
        for metric in MetricData:
            print(
                f"[LOCAL METRIC] Namespace={Namespace} | "
                f"Name={metric['MetricName']} | "
                f"Value={metric['Value']} {metric.get('Unit', '')}"
            )

if is_prod():
    _cloudwatch = boto3.client("cloudwatch", region_name="us-west-2")
else:
    _logger.info("Using MockCloudWatchClient for local development")
    _cloudwatch = MockCloudWatchClient()


class _Metric(ABC):
    def __init__(self, name: str, unit: str):
        self._name = name
        self._unit = unit

    def _put(self, value: int | float, dimensions: dict[str, str] | None = None):
        try:
            _cloudwatch.put_metric_data(
                Namespace=settings.project_name,
                MetricData=[{
                    "MetricName": self._name,
                    "Value": value,
                    "Unit": self._unit,
                    "Dimensions": [{"Name": k, "Value": v} for k, v in (dimensions or {}).items()]
                }]
            )
        except Exception as e:
            _logger.error(f"Failed to send metric '{self._name}' to CloudWatch: {e}")


class _Gauge(_Metric):
    def __init__(self, name: str, unit: str = "Count"):
        super().__init__(name, unit)

    def update(self, value: float, dimensions: dict[str, str] | None = None):
        self._put(value, dimensions)


class _Counter(_Metric):
    def __init__(self, name: str, unit: str = "Count"):
        super().__init__(name, unit)

    def increment(self, value: int = 1, dimensions: dict[str, str] | None = None):
        self._put(value, dimensions)


class _Latency(_Metric):
    class _LatencyMeasurer:
        def __init__(self, latency_metric: '_Latency'):
            self._latency_metric = latency_metric
            self._start_time = None

        def __enter__(self):
            self._start_time = time.time()
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            if not exc_val and self._start_time is not None:
                elapsed_time_ms = (time.time() - self._start_time) * 1000  # Convert to milliseconds
                self._latency_metric.record(elapsed_time_ms)

    def __init__(self, name: str):
        super().__init__(name, unit = "Milliseconds")

    def record(self, value: float, dimensions: dict[str, str] | None = None):
        self._put(value, dimensions)

    def measure(self) -> _LatencyMeasurer:
        return self._LatencyMeasurer(self)


user_signup = _Counter("user_signup")
user_login = _Counter("user_login")
user_total = _Gauge("user_total")