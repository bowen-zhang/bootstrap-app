import os

import fastapi
import uvicorn

from protos import api_connect
from services.api.account_service import AccountService
from services.api.auth_interceptor import AuthInterceptor
from services.api.greeting_service import GreetingService
from shared.settings import settings, is_dev


def create_app():
    app = fastapi.FastAPI()
    greeting_service_app = api_connect.GreetingServiceASGIApplication(
        GreetingService(),
        interceptors=[AuthInterceptor()],
    )
    account_service_app = api_connect.AccountServiceASGIApplication(
        AccountService(),
        interceptors=[AuthInterceptor()],
    )
    app.mount('/app.v1.GreetingService', greeting_service_app)
    app.mount('/app.v1.AccountService', account_service_app)
    for route in app.routes:
        print(f'Registered route: {route.path}')

    return app


if __name__ == "__main__":
    uvicorn.run(
        "main:create_app",
        factory=True,
        host="localhost", 
        port = settings.api_service_settings.port,
        reload=is_dev(),
    )
