import fastapi
import os
import sys
import uvicorn

from connectrpc.request import RequestContext
from connectrpc.compat import google_protobuf_codecs

from protos import api_connect, api_pb2
from shared.settings import settings


class GreetingService(api_connect.GreetingService):
    async def greet(
        self, request: api_pb2.GreetRequest, ctx: RequestContext
    ) -> api_pb2.GreetResponse:
        del ctx
        name = request.name.strip() or "world"
        return api_pb2.GreetResponse(message=f"Hello, {name}!")


def create_app():
    app = fastapi.FastAPI()
    greeting_service_app = api_connect.GreetingServiceASGIApplication(GreetingService())
    app.mount('/app.v1.GreetingService', greeting_service_app)
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
