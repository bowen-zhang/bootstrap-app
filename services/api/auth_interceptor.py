from __future__ import annotations

from typing import Any

from connectrpc.code import Code
from connectrpc.errors import ConnectError
from connectrpc.interceptor import UnaryInterceptor
from connectrpc.request import RequestContext

from protos import account_pb, storage_pb
from services.api import auth_utils
from services.api.connectrpc_utils import _get_cookie


_WHITE_LIST = {
    "app.v1.AccountService/Create",
    "app.v1.AccountService/Login",
    "app.v1.AccountService/RefreshToken",
    "app.v1.AccountService/Logout",
}


class AuthInterceptor(UnaryInterceptor):
    async def intercept_unary(self, call_next, request, ctx: RequestContext):
        method_key = f"{ctx.method.service_name}/{ctx.method.name}"
        if method_key in _WHITE_LIST:
            return await call_next(request, ctx)

        account_id = auth_utils.get_access_token(ctx)
        setattr(ctx, "account_id", account_id)
        return await call_next(request, ctx)


def get_account_id(ctx: RequestContext) -> str:
    if not hasattr(ctx, "account_id"):
        raise ConnectError(code=Code.UNAUTHENTICATED, message="Missing account_id in context")
    return getattr(ctx, "account_id")


def get_account(storage_service_client, ctx: RequestContext) -> account_pb.Account:
    account_id = get_account_id(ctx)
    account = storage_service_client.get(storage_pb.GetRequest(
        id=account_id,
        subject_type=storage_pb.SubjectType.ACCOUNT
    )).subject.value
    if account is None:
        raise ConnectError(code=Code.UNAUTHENTICATED, message="Account not found")
    return account