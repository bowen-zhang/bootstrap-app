import jwt
import uuid
from typing import Optional

from connectrpc.request import RequestContext
from fastapi import HTTPException
from http.cookies import SimpleCookie

from protos import api_connect, api_pb2, storage_pb2
from services.api import auth_utils


class AccountService(api_connect.AccountService):
    _accounts: dict[str, storage_pb2.Account] = {}

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

        account_id = str(uuid.uuid4())
        account = storage_pb2.Account(
            id=account_id,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
        )
        self._accounts[email] = account

        self._set_tokens(account_id, ctx)
        return api_pb2.CreateAccountResponse(
            account_id=account_id,
            email=email,
            first_name=first_name,
            last_name=last_name,
        )

    async def login(
        self, request: api_pb2.LoginRequest, ctx: RequestContext
    ) -> api_pb2.LoginResponse:
        email = request.email.strip()
        password = request.password

        account = self._accounts.get(email)
        if account is None:
            raise HTTPException(status_code=401, detail="Invalid email or password")
        if password != account.password:
            raise HTTPException(status_code=401, detail="Invalid email or password")

        self._set_tokens(email, ctx)
        return api_pb2.LoginResponse(
            account_id=email,
            email=email,
            first_name=account.first_name,
            last_name=account.last_name,
        )

    async def refresh_token(
        self, request: api_pb2.RefreshTokenRequest, ctx: RequestContext
    ) -> api_pb2.RefreshTokenResponse:
        raw_cookie_header = ctx.request_headers().get("cookie")
        if not raw_cookie_header:
            raise HTTPException(status_code=401, detail="No cookies found in request")

        cookie = SimpleCookie()
        cookie.load(raw_cookie_header)
        if "refresh_token" not in cookie:
            raise HTTPException(status_code=401, detail="Refresh token cookie not found")

        refresh_token = cookie["refresh_token"].value
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
        access_token = auth_utils.create_access_token(user_id)
        refresh_token = auth_utils.create_refresh_token(user_id)

        access_token_cookie = self._build_cookie(
            name="access_token",
            value=access_token,
            path="/",
            httponly=True,
            secure=True,
            samesite="Strict"
        )
        refresh_token_cookie = self._build_cookie(
            name="refresh_token",
            value=refresh_token,
            path="/api/app.v1.AccountingService/RefreshToken",
            httponly=True,
            secure=True,
            samesite="Strict"
        )

        ctx.response_headers.add("Set-Cookie", access_token_cookie)
        ctx.response_headers.add("Set-Cookie", refresh_token_cookie)

        print(f"Set access_token and refresh_token cookies for user_id: {user_id}")

    def _clear_tokens(self, ctx: RequestContext) -> None:
        cookies = [
            self._build_cookie(
                name="access_token",
                value="",
                path="/",
                httponly=True,
                secure=True,
                samesite="Strict",
                max_age=0
            ),
            self._build_cookie(
                name="refresh_token",
                value="",
                path="/api/app.v1.AccountingService/RefreshToken",
                httponly=True,
                secure=True,
                samesite="Strict",
                max_age=0
            )
        ]
        ctx.response_headers["Set-Cookie"] = '\n'.join(cookies)

    def _build_cookie(
        self,
        name: str, 
        value: str, 
        path: str = "/", 
        httponly: bool = True, 
        secure: bool = True, 
        samesite: str = "Strict", 
        max_age: Optional[int] = None
    ) -> str:
        """Generates a perfectly formatted Set-Cookie header string."""
        cookie = SimpleCookie()
        cookie[name] = value
        
        # SimpleCookie requires lowercase attribute keys
        cookie[name]["path"] = path
        cookie[name]["httponly"] = httponly
        cookie[name]["secure"] = secure
        cookie[name]["samesite"] = samesite
        
        if max_age is not None:
            cookie[name]["max-age"] = max_age
            
        return cookie[name].OutputString()