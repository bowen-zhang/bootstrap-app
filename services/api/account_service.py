import logging

from connectrpc.request import RequestContext
from fastapi import HTTPException

from protobuf import wkt, Oneof
from protos import account_pb, api_connect, api_pb, storage_pb
from services.api import auth_utils
from shared import metrics


_logger = logging.getLogger(__name__)


class AccountService(api_connect.AccountService):
    def __init__(self, storage_service_client):
        self._storage = storage_service_client

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
        account = self._find_by_email(email)
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
                    account.deleted_at = None
                    self._storage.update(storage_pb.UpdateRequest(
                        subject=Oneof("account", account)
                    ))
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
            result = self._storage.insert(storage_pb.InsertRequest(
                subject=Oneof("account", account)
            ))
            account.id = result.id

            # Update metrics
            metrics.user_signup.increment()
            total_count = self._storage.count(storage_pb.CountRequest(
                subject_type=storage_pb.SubjectType.ACCOUNT
            )).count
            metrics.user_total.update(total_count)

            _logger.warning(f"NEW-ACCOUNT: id={account.id}, email={account.email}")

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

        account = self._find_by_email(email)
        if account is None:
            raise HTTPException(status_code=401, detail="Invalid email or password")
        if password != account.password:
            raise HTTPException(status_code=401, detail="Invalid email or password")
        if account.status != account_pb.AccountStatus.ACTIVE:
            raise HTTPException(status_code=403, detail="Account is not active")

        account.last_accessed_at = wkt.Timestamp().now()
        self._storage.update(storage_pb.UpdateRequest(
            subject=Oneof("account", account)
        ))

        metrics.user_login.increment()

        auth_utils.set_tokens(ctx, account.id)

        return api_pb.LoginResponse(
            account_id=account.id,
            email=account.email,
            first_name=account.first_name,
            last_name=account.last_name,
        )

    async def get_current_user(
        self, request: api_pb.GetCurrentUserRequest, ctx: RequestContext
    ) -> api_pb.GetCurrentUserResponse:
        account = auth_utils.get_account(self._storage, ctx)
        return api_pb.GetCurrentUserResponse(
            account_id=account.id,
            email=account.email,
            first_name=account.first_name,
            last_name=account.last_name,
        )

    async def refresh_token(
        self, request: api_pb.RefreshTokenRequest, ctx: RequestContext
    ) -> api_pb.RefreshTokenResponse:
        account = auth_utils.get_account(self._storage, ctx)
        auth_utils.set_tokens(ctx, account.id)
        return api_pb.RefreshTokenResponse()

    async def logout(
        self, request: api_pb.LogoutRequest, ctx: RequestContext
    ) -> api_pb.LogoutResponse:
        auth_utils.clear_tokens(ctx)
        return api_pb.LogoutResponse()

    def _find_by_email(self, email: str) -> account_pb.Account | None:
        response = self._storage.list(storage_pb.ListRequest(
            subject_type=storage_pb.SubjectType.ACCOUNT,
            filter=Oneof("account_filter", storage_pb.AccountFilter(email=email))
        ))
        if response.accounts:
            return response.accounts[0]
        return None

