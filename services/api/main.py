import os

import fastapi
import uvicorn

from protos import api_connect
from shared.settings import settings

try:
    from .account_service import AccountService
    from .greeting_service import GreetingService
except ImportError:
    from account_service import AccountService
    from greeting_service import GreetingService


def create_app():
    app = fastapi.FastAPI()
    greeting_service_app = api_connect.GreetingServiceASGIApplication(GreetingService())
    account_service_app = api_connect.AccountServiceASGIApplication(AccountService())
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
        port = int(os.getenv("PORT", "50051")),
        reload=settings.is_dev
    )
