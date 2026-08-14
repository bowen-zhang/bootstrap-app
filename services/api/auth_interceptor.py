from __future__ import annotations

from typing import Any

from connectrpc.code import Code
from connectrpc.errors import ConnectError
from connectrpc.interceptor import UnaryInterceptor
from connectrpc.request import RequestContext

from protos import account_pb2
from services.api import auth_utils
from services.api.account_storage import account_storage
from services.api.connectrpc_utils import _get_cookie


_WHITE_LIST = {
    "app.v1.AccountService/Create",
    "app.v1.AccountService/Login",
}


class AuthInterceptor(UnaryInterceptor):
    async def intercept_unary(self, call_next, request, ctx: RequestContext):
        method_key = f"{ctx.method.service_name}/{ctx.method.name}"
        if method_key in _WHITE_LIST:
            return await call_next(request, ctx)

        token = _get_cookie(ctx, "access_token")
        if not token:
            raise ConnectError(Code.UNAUTHENTICATED, "Missing access token")

        try:
            account_id = auth_utils.validate_access_token(token)
        except Exception as exc:
            raise ConnectError(Code.UNAUTHENTICATED, str(exc)) from exc

        setattr(ctx, "account_id", account_id)
        return await call_next(request, ctx)


def get_account_id(ctx: RequestContext) -> str:
    if not hasattr(ctx, "account_id"):
        raise ConnectError(Code.UNAUTHENTICATED, "Missing account_id in context")
    return getattr(ctx, "account_id")


def get_account(ctx: RequestContext) -> account_pb2.Account:
    account_id = get_account_id(ctx)
    account = account_storage.get_by_id(account_id)
    if account is None:
        raise ConnectError(Code.UNAUTHENTICATED, "Account not found")
    return account