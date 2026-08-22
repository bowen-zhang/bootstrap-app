from connectrpc.request import RequestContext
from fastapi import HTTPException

from protobuf import wkt
from protos import account_pb, api_connect, api_pb
from services.api import auth_utils
from services.api.account_storage import account_storage


class AccountService(api_connect.AccountService):
    async def create(
        self, request: api_pb.CreateAccountRequest, ctx: RequestContext
    ) -> api_pb.CreateAccountResponse:
        email = request.email.strip()
        password = request.password
        first_name = request.first_name.strip()
        last_name = request.last_name.strip()

        if not email:
            raise Exception("Email cannot be empty")
        if not password:
            raise Exception("Password cannot be empty")

        # Check if the account already exists
        account = account_storage.get_by_email(email)
        if account is not None:
            match account.status:
                case account_pb.AccountStatus.ACTIVE:
                    raise Exception("Account with this email already exists")
                case account_pb.AccountStatus.SUSPENDED:
                    raise Exception("Account with this email is suspended")
                case account_pb.AccountStatus.DELETED:
                    # If the account was deleted, we can allow re-creation
                    account.password = password
                    account.first_name = first_name
                    account.last_name = last_name
                    account.status = account_pb.AccountStatus.ACTIVE
                    account.last_accessed_at = wkt.Timestamp().now()
                    account.deleted_at.Clear()
                    account_storage.update(account)
                case _:
                    raise Exception("Account with this email has an unknown status")
        else:
            # Create a new account
            account = account_pb.Account(
                status=account_pb.AccountStatus.ACTIVE,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
            )
            account.created_at = wkt.Timestamp().now()
            account.last_accessed_at = wkt.Timestamp().now()
            account = account_storage.create_account(account)

        auth_utils.set_tokens(ctx, account.id)

        return api_pb.CreateAccountResponse(
            account_id=account.id,
            email=account.email,
            first_name=account.first_name,
            last_name=account.last_name,
        )

    async def login(
        self, request: api_pb.LoginRequest, ctx: RequestContext
    ) -> api_pb.LoginResponse:
        email = request.email.strip()
        password = request.password

        account = account_storage.get_by_email(email)
        if account is None:
            raise HTTPException(status_code=401, detail="Invalid email or password")
        if password != account.password:
            raise HTTPException(status_code=401, detail="Invalid email or password")
        if account.status != account_pb.AccountStatus.ACTIVE:
            raise HTTPException(status_code=403, detail="Account is not active")

        account.last_accessed_at = wkt.Timestamp().now()
        account_storage.update(account)

        auth_utils.set_tokens(ctx, account.id)

        return api_pb.LoginResponse(
            account_id=account.id,
            email=account.email,
            first_name=account.first_name,
            last_name=account.last_name,
        )

    async def refresh_token(
        self, request: api_pb.RefreshTokenRequest, ctx: RequestContext
    ) -> api_pb.RefreshTokenResponse:
        account_id = auth_utils.get_refresh_token(ctx)

        # Validate account
        account = account_storage.get_by_id(account_id)
        if account is None:
            raise HTTPException(status_code=401, detail="Account not found")
        if account.status != account_pb.AccountStatus.ACTIVE:
            raise HTTPException(status_code=403, detail="Account is not active")

        auth_utils.set_tokens(ctx, account_id)

        return api_pb.RefreshTokenResponse()

    async def logout(
        self, request: api_pb.LogoutRequest, ctx: RequestContext
    ) -> api_pb.LogoutResponse:
        auth_utils.clear_tokens(ctx)
        return api_pb.LogoutResponse()

