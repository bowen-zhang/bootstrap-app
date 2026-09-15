import logging

from hypercorn import config, run
from protos import api_connect, api_pb, storage_connect
from services.api.account_service import AccountService
from services.api.auth_interceptor import AuthInterceptor
from services.api.greeting_service import GreetingService
from shared.settings import settings, is_dev
from third_party.bootstrap_utils import app_utils

_logger = logging.getLogger(__name__)


def create_app() -> app_utils.ServerApp:

    account_service_fullname = api_connect.AccountServiceASGIApplication.path.fget(None).lstrip("/")
    token_refresh_method = f"{account_service_fullname}/RefreshToken"
    whitelist_methods = [
        f"{account_service_fullname}/Create",
        f"{account_service_fullname}/Login",
        f"{account_service_fullname}/RefreshToken",
        f"{account_service_fullname}/Logout",
    ]
    auth_interceptor = AuthInterceptor(
        token_refresh_method=token_refresh_method,
        whitelist_methods=whitelist_methods
    )

    storage_service_client = storage_connect.StorageServiceClientSync(
        f"http://{settings.storage_service_settings.hostname}:{settings.storage_service_settings.port}"
    )
    greeting_service_app = api_connect.GreetingServiceASGIApplication(
        GreetingService(storage_service_client),
        interceptors=[auth_interceptor],
    )
    account_service_app = api_connect.AccountServiceASGIApplication(
        AccountService(storage_service_client),
        interceptors=[auth_interceptor],
    )
    app = app_utils.ServerApp(
        apps=[account_service_app, greeting_service_app],
        descriptors=[api_pb.desc()],
        dev=is_dev(),
    )

    return app


app = create_app()


if __name__ == "__main__":
    config = config.Config()
    config.bind = [f"0.0.0.0:{settings.api_service_settings.port}"]
    config.use_reloader = is_dev()
    config.application_path = "main:app"
    config.graceful_timeout = 3
    run.run(config)
