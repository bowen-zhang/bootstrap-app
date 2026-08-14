from connectrpc.request import RequestContext

from protos import api_connect, api_pb2
from services.api.auth_interceptor import get_account


class GreetingService(api_connect.GreetingService):
    async def greet(
        self, request: api_pb2.GreetRequest, ctx: RequestContext
    ) -> api_pb2.GreetResponse:
        account = get_account(ctx)
        return api_pb2.GreetResponse(message=f"Hello, {account.first_name}!")
