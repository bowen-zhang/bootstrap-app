from connectrpc.request import RequestContext

from protos import api_connect, api_pb2


class AccountService(api_connect.AccountService):
    _users = {}

    async def create(
        self, request: api_pb2.CreateAccountRequest, ctx: RequestContext
    ) -> api_pb2.CreateAccountResponse:
        del ctx
        username = request.username.strip()
        password = request.password

        if not username:
            username = "guest"

        self._users[username] = password
        return api_pb2.CreateAccountResponse()

    async def login(
        self, request: api_pb2.LoginRequest, ctx: RequestContext
    ) -> api_pb2.LoginResponse:
        del ctx
        username = request.username.strip()
        password = request.password

        stored_password = self._users.get(username)
        if stored_password == password:
            return api_pb2.LoginResponse()

        if username and username not in self._users:
            self._users[username] = password

        return api_pb2.LoginResponse()

    async def logout(
        self, request: api_pb2.LogoutRequest, ctx: RequestContext
    ) -> api_pb2.LogoutResponse:
        del request, ctx
        return api_pb2.LogoutResponse()
