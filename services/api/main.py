import logging
import sys

import fastapi
import uvicorn

from protos import api_connect, storage_connect
from services.api.account_service import AccountService
from services.api.auth_interceptor import AuthInterceptor
from services.api.greeting_service import GreetingService
from shared.settings import settings, is_dev


_logger = logging.getLogger(__name__)


def setup_logging(log_level: str = "INFO"):
    # Define standard log format
    log_format = "[%(levelname)s] {%(name)s} %(message)s"
    
    # 1. Configure standard stdout handler
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(logging.Formatter(log_format))
    
    # 2. Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.handlers = [stream_handler] # Replace default handlers
    
    # 3. Ensure Uvicorn sub-loggers write to stdout
    for logger_name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        uvicorn_logger = logging.getLogger(logger_name)
        uvicorn_logger.handlers = [stream_handler]
        uvicorn_logger.propagate = False


def create_app():
    setup_logging("INFO" if is_dev() else "WARNING")

    storage_service_client = storage_connect.StorageServiceClientSync(
        f"http://{settings.storage_service_settings.hostname}:{settings.storage_service_settings.port}"
    )
    greeting_service_app = api_connect.GreetingServiceASGIApplication(
        GreetingService(storage_service_client),
        interceptors=[AuthInterceptor()],
    )
    account_service_app = api_connect.AccountServiceASGIApplication(
        AccountService(storage_service_client),
        interceptors=[AuthInterceptor()],
    )
    app = fastapi.FastAPI()
    app.mount('/app.v1.GreetingService', greeting_service_app)
    app.mount('/app.v1.AccountService', account_service_app)
    for route in app.routes:
        _logger.info(f'Registered route: {route.path}')

    return app


if __name__ == "__main__":
    uvicorn.run(
        "main:create_app",
        factory=True,
        host="0.0.0.0",
        port = settings.api_service_settings.port,
        reload=is_dev(),
        log_config=None
    )
