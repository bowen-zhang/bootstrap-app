import logging

from protos import api_connect, api_pb, storage_connect
from services.api import account_utils
from services.api.account_service import AccountService
from services.api.greeting_service import GreetingService
from shared.common import settings, is_dev
from third_party.bootstrap_utils import app_utils, auth_utils

_logger = logging.getLogger(__name__)


def create_app() -> app_utils.ServerApp:
    storage_service_client = storage_connect.StorageServiceClient(
        f"http://{settings.storage_service_settings.hostname}:{settings.storage_service_settings.port}"
    )

    account_service_fullname = api_connect.AccountServiceASGIApplication.path.fget(None).lstrip("/")
    token_refresh_method = f"{account_service_fullname}/RefreshToken"
    api_key_methods = []
    whitelist_methods = [
        f"{account_service_fullname}/Create",
        f"{account_service_fullname}/Login",
        f"{account_service_fullname}/RefreshToken",
        f"{account_service_fullname}/Logout",
    ]
    assert(settings.api_service_settings)
    assert(settings.api_service_settings.jwt_settings)
    auth_reader = auth_utils.ServerAuthReader(
        secret=settings.api_service_settings.jwt_settings.secret,
        algorithm=settings.api_service_settings.jwt_settings.algorithm,
    )
    api_key_manager = account_utils.ApiKeyManager(storage_service_client)
    auth_interceptor = auth_utils.ServerAuthInterceptor(
        auth_reader=auth_reader,
        api_key_lookup=api_key_manager.lookup,
        token_refresh_method=token_refresh_method,
        api_key_methods=api_key_methods,
        whitelist_methods=whitelist_methods
    )    

    account_service = AccountService(
        storage_service_client=storage_service_client,
        api_key_manager=api_key_manager
    )
    account_service_app = api_connect.AccountServiceASGIApplication(
        account_service,
        interceptors=[auth_interceptor],
    )
    greeting_service_app = api_connect.GreetingServiceASGIApplication(
        GreetingService(storage_service_client),
        interceptors=[auth_interceptor],
    )
    app = app_utils.ServerApp(
        apps=[account_service_app, greeting_service_app],
        descriptors=[api_pb.desc()],
        dev=is_dev(),
    )

    return app


if __name__ == "__main__":
    assert(settings.api_service_settings)
    app_utils.run_app(
        app_entry="main:create_app()",
        port=settings.api_service_settings.port,
        dev=is_dev()
    )
