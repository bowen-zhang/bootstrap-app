from __future__ import annotations

import logging

from connectrpc.interceptor import UnaryInterceptor
from connectrpc.request import RequestContext

from services.api import auth_utils
from services.api.connectrpc_utils import _get_cookie


_TOKEN_REFRESH_METHOD = "app.v1.AccountService/RefreshToken"

_WHITE_LIST = {
    "app.v1.AccountService/Create",
    "app.v1.AccountService/Login",
    "app.v1.AccountService/RefreshToken",
    "app.v1.AccountService/Logout",
}

_logger = logging.getLogger(__name__)


class AuthInterceptor(UnaryInterceptor):
    async def intercept_unary(self, call_next, request, ctx: RequestContext):
        method = f"{ctx.method.service_name}/{ctx.method.name}"
        if method == _TOKEN_REFRESH_METHOD:
            account_id = auth_utils.get_refresh_token(ctx)
            auth_utils.set_account_id(ctx, account_id)
            return await call_next(request, ctx)    
        elif method in _WHITE_LIST:
            _logger.info(f"Skipping auth check for whitelisted method: {method}")
            return await call_next(request, ctx)
        else:
            account_id = auth_utils.get_access_token(ctx)
            auth_utils.set_account_id(ctx, account_id)
            return await call_next(request, ctx)


