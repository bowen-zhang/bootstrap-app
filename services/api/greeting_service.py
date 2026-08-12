from connectrpc.request import RequestContext

from protos import api_connect, api_pb2


class GreetingService(api_connect.GreetingService):
    async def greet(
        self, request: api_pb2.GreetRequest, ctx: RequestContext
    ) -> api_pb2.GreetResponse:
        del ctx
        name = request.name.strip() or "world"
        return api_pb2.GreetResponse(message=f"Hello, {name}!")
