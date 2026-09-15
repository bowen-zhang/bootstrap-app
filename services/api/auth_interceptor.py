from __future__ import annotations

import logging

from connectrpc.interceptor import MetadataInterceptor
from connectrpc.request import RequestContext

from services.api import auth_utils
from services.api.connectrpc_utils import _get_cookie


_logger = logging.getLogger(__name__)


class AuthInterceptor(MetadataInterceptor):
    def __init__(self, token_refresh_method: str, whitelist_methods: list[str] | None = None) -> None:
        self._token_refresh_method = token_refresh_method
        self._whitelist_methods = set(whitelist_methods or [])

    async def on_start(self, ctx: RequestContext) -> None:
        method = f"{ctx.method.service_name}/{ctx.method.name}"
        if method == self._token_refresh_method:
            account_id = auth_utils.get_refresh_token(ctx)
            auth_utils.set_account_id(ctx, account_id)
        elif method in self._whitelist_methods:
            _logger.info(f"Skipping auth check for whitelisted method: {method}")
        else:
            account_id = auth_utils.get_access_token(ctx)
            auth_utils.set_account_id(ctx, account_id)


