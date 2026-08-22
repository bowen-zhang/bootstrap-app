from connectrpc.request import RequestContext

from protos import api_connect, api_pb
from services.api.auth_interceptor import get_account


class GreetingService(api_connect.GreetingService):
    def __init__(self, storage_service_client):
        self._storage = storage_service_client

    async def greet(
        self, request: api_pb.GreetRequest, ctx: RequestContext
    ) -> api_pb.GreetResponse:
        account = get_account(self._storage, ctx)
        return api_pb.GreetResponse(message=f"Hello, {account.first_name}!")
