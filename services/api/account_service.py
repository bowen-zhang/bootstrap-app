from connectrpc.request import RequestContext
from fastapi import HTTPException

from protos import account_pb2, api_connect, api_pb2
from services.api import auth_utils
from services.api.account_storage import account_storage
from services.api.connectrpc_utils import _get_cookie, _set_cookie
from shared.settings import settings


class AccountService(api_connect.AccountService):
    async def create(
        self, request: api_pb2.CreateAccountRequest, ctx: RequestContext
    ) -> api_pb2.CreateAccountResponse:
        email = request.email.strip()
        password = request.password
        first_name = request.first_name.strip()
        last_name = request.last_name.strip()

        if not email:
            raise Exception("Email cannot be empty")
        if not password:
            raise Exception("Password cannot be empty")

        account = account_pb2.Account(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
        )
        account = account_storage.create_account(account)

        self._set_tokens(account.id, ctx)
        return api_pb2.CreateAccountResponse(
            account_id=account.id,
            email=account.email,
            first_name=account.first_name,
            last_name=account.last_name,
        )

    async def login(
        self, request: api_pb2.LoginRequest, ctx: RequestContext
    ) -> api_pb2.LoginResponse:
        email = request.email.strip()
        password = request.password

        account = account_storage.get_by_email(email)
        if account is None:
            raise HTTPException(status_code=401, detail="Invalid email or password")
        if password != account.password:
            raise HTTPException(status_code=401, detail="Invalid email or password")

        self._set_tokens(account.id, ctx)
        return api_pb2.LoginResponse(
            account_id=account.id,
            email=account.email,
            first_name=account.first_name,
            last_name=account.last_name,
        )

    async def refresh_token(
        self, request: api_pb2.RefreshTokenRequest, ctx: RequestContext
    ) -> api_pb2.RefreshTokenResponse:
        refresh_token = _get_cookie(ctx, "refresh_token")
        if not refresh_token:
            raise HTTPException(status_code=401, detail="Refresh token missing")

        try:
            payload = auth_utils.validate_refresh_token(refresh_token)
        except Exception as ex:
                raise HTTPException(status_code=401, detail=str(ex))

        user_id = payload.get("sub")
        self._set_tokens(user_id, ctx)
        return api_pb2.RefreshTokenResponse()

    async def logout(
        self, request: api_pb2.LogoutRequest, ctx: RequestContext
    ) -> api_pb2.LogoutResponse:
        self._clear_tokens(ctx)
        return api_pb2.LogoutResponse()

    def _set_tokens(self, user_id: str, ctx: RequestContext) -> None:
        _set_cookie(
            ctx,
            name="access_token",
            value=auth_utils.create_access_token(user_id),
            path="/",
            httponly=True,
            secure=True,
            samesite="Strict",
            max_age=settings.jwt_settings.access_token_expiration_seconds
        )
        _set_cookie(
            ctx,
            name="refresh_token",
            value=auth_utils.create_refresh_token(user_id),
            path="/api/app.v1.AccountService/RefreshToken",
            httponly=True,
            secure=True,
            samesite="Strict",
            max_age=settings.jwt_settings.refresh_token_expiration_seconds
        )

    def _clear_tokens(self, ctx: RequestContext) -> None:
        _set_cookie(
            ctx,
            name="access_token",
            value="",
            path="/",
            httponly=True,
            secure=True,
            samesite="Strict",
            max_age=0
        )
        _set_cookie(
            ctx,
            name="refresh_token",
            value="",
            path="/api/app.v1.AccountService/RefreshToken",
            httponly=True,
            secure=True,
            samesite="Strict",
            max_age=0
        )

