import os

import fastapi
import uvicorn

from protos import api_connect, storage_connect
from services.api.account_service import AccountService
from services.api.auth_interceptor import AuthInterceptor
from services.api.greeting_service import GreetingService
from shared.settings import settings, is_dev


def create_app():
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
        print(f'Registered route: {route.path}')

    return app


if __name__ == "__main__":
    uvicorn.run(
        "main:create_app",
        factory=True,
        host="0.0.0.0",
        port = settings.api_service_settings.port,
        reload=is_dev(),
    )
