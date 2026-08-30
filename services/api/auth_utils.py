import datetime

import jwt
from connectrpc.code import Code
from connectrpc.errors import ConnectError
from connectrpc.request import RequestContext

from protos import account_pb, storage_pb
from services.api.connectrpc_utils import _get_cookie, _set_cookie
from shared.settings import settings


_ACCESS_TOKEN_COOKIE_NAME = "access_token"
_REFRESH_TOKEN_COOKIE_NAME = "refresh_token"
_REFRESH_TOKEN_PATH = "/api/app.v1.AccountService/RefreshToken"

_jwt_settings = settings.api_service_settings.jwt_settings


_CONTEXT_ACCOUNT_ID_KEY = "account_id"


def set_account_id(ctx: RequestContext, account_id: str) -> None:
    setattr(ctx, _CONTEXT_ACCOUNT_ID_KEY, account_id)


def get_account_id(ctx: RequestContext) -> str:
    if not hasattr(ctx, _CONTEXT_ACCOUNT_ID_KEY):
        raise ConnectError(code=Code.UNAUTHENTICATED, message="Missing account_id in context")
    return getattr(ctx, _CONTEXT_ACCOUNT_ID_KEY)


def get_account(storage_service_client, ctx: RequestContext) -> account_pb.Account:
    account_id = get_account_id(ctx)
    account = storage_service_client.get(storage_pb.GetRequest(
        id=account_id,
        subject_type=storage_pb.SubjectType.ACCOUNT
    )).subject.value
    if account is None:
        raise ConnectError(code=Code.UNAUTHENTICATED, message="Account not found")
    if account.status != account_pb.AccountStatus.ACTIVE:
        raise ConnectError(code=Code.PERMISSION_DENIED, message="Account is not active")
    return account


def set_tokens(ctx: RequestContext, user_id: str) -> None:
    _set_cookie(
        ctx,
        name=_ACCESS_TOKEN_COOKIE_NAME,
        value=_create_access_token(user_id),
        path="/",
        httponly=True,
        secure=True,
        samesite="Strict",
        max_age=_jwt_settings.access_token_expiration_seconds,
    )
    _set_cookie(
        ctx,
        name=_REFRESH_TOKEN_COOKIE_NAME,
        value=_create_refresh_token(user_id),
        path=_REFRESH_TOKEN_PATH,
        httponly=True,
        secure=True,
        samesite="Strict",
        max_age=_jwt_settings.refresh_token_expiration_seconds,
    )


def clear_tokens(ctx: RequestContext) -> None:
    _set_cookie(
        ctx,
        name=_ACCESS_TOKEN_COOKIE_NAME,
        value="",
        path="/",
        httponly=True,
        secure=True,
        samesite="Strict",
        max_age=0,
    )
    _set_cookie(
        ctx,
        name=_REFRESH_TOKEN_COOKIE_NAME,
        value="",
        path=_REFRESH_TOKEN_PATH,
        httponly=True,
        secure=True,
        samesite="Strict",
        max_age=0,
    )


def get_access_token(ctx: RequestContext) -> str:
    token = _get_cookie(ctx, _ACCESS_TOKEN_COOKIE_NAME)
    if not token:
        raise ConnectError(code=Code.UNAUTHENTICATED, message="Access token missing")

    try:
        account_id = _validate_access_token(token)
    except Exception as ex:
        raise ConnectError(code=Code.UNAUTHENTICATED, message=str(ex))

    return account_id


def get_refresh_token(ctx: RequestContext) -> str:
    token = _get_cookie(ctx, _REFRESH_TOKEN_COOKIE_NAME)
    if not token:
        raise ConnectError(code=Code.UNAUTHENTICATED, message="Refresh token missing")

    try:
        account_id = _validate_refresh_token(token)
    except Exception as ex:
        raise ConnectError(code=Code.UNAUTHENTICATED, message=str(ex))

    return account_id


def _create_access_token(account_id: str, extra_claims: dict = None) -> str:
    payload = {
        "sub": account_id,  # Subject (User ID)
        "type": "access",
        "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(seconds=_jwt_settings.access_token_expiration_seconds),
        "iat": datetime.datetime.now(datetime.timezone.utc),
    }
    if extra_claims:
        payload.update(extra_claims)
        
    return jwt.encode(payload, _jwt_settings.secret, algorithm=_jwt_settings.algorithm)


def _create_refresh_token(account_id: str) -> str:
    payload = {
        "sub": account_id,
        "type": "refresh",
        "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(seconds=_jwt_settings.refresh_token_expiration_seconds),
        "iat": datetime.datetime.now(datetime.timezone.utc),
    }
    return jwt.encode(payload, _jwt_settings.secret, algorithm=_jwt_settings.algorithm)


def _validate_access_token(token: str) -> str:
    return _validate_token(token, expected_type="access")


def _validate_refresh_token(token: str) -> str:
    return _validate_token(token, expected_type="refresh")


def _validate_token(token: str, expected_type: str) -> str:
    try:
        payload = jwt.decode(token, _jwt_settings.secret, algorithms=[_jwt_settings.algorithm])
        if payload.get("type") != expected_type:
            raise ConnectError(code=Code.UNAUTHENTICATED, message=f"Invalid {expected_type} token type")
        return payload.get("sub")
    except jwt.ExpiredSignatureError:
        raise ConnectError(code=Code.UNAUTHENTICATED, message=f"{expected_type.capitalize()} token has expired")
    except jwt.InvalidTokenError as e:
        raise ConnectError(code=Code.UNAUTHENTICATED, message=f"Invalid {expected_type} token")