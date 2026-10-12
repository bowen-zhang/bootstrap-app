import logging

from connectrpc.request import RequestContext
from fastapi import HTTPException
from protobuf import wkt, Oneof
from protos import account_pb, api_connect, api_pb, storage_connect, storage_pb
from services.api import account_utils
from shared.common import metric_builder, settings
from third_party.bootstrap_utils import auth_utils as auth_utils


_ACCOUNT_SERVICE_FULLNAME = api_connect.AccountServiceASGIApplication.path.fget(None).lstrip("/")
_REFRESH_TOKEN_PATH = f"/api/{_ACCOUNT_SERVICE_FULLNAME}/RefreshToken"

_logger = logging.getLogger(__name__)


class AccountService(api_connect.AccountService):
    _user_signup = metric_builder.counter("user_signup")
    _user_login = metric_builder.counter("user_login")
    _user_total = metric_builder.gauge("user_total")

    _storage: storage_connect.StorageServiceClient
    _auth_writer: auth_utils.ServerAuthWriter

    def __init__(
            self,
            storage_service_client: storage_connect.StorageServiceClient,
            api_key_manager: account_utils.ApiKeyManager
        ):
        self._storage = storage_service_client
        self._api_key_manager = api_key_manager

        assert(settings.api_service_settings)
        assert(settings.api_service_settings.jwt_settings)
        jwt_settings = settings.api_service_settings.jwt_settings

        self._auth_writer = auth_utils.ServerAuthWriter(
            secret=jwt_settings.secret,
            algorithm=jwt_settings.algorithm,
            access_token_expiration_seconds=jwt_settings.access_token_expiration_seconds,
            refresh_token_expiration_seconds=jwt_settings.refresh_token_expiration_seconds,
            refresh_token_path=_REFRESH_TOKEN_PATH
        )

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
        account = await self._find_by_email(email)
        if account is not None:
            match account.status:
                case account_pb.AccountStatus.ACTIVE:
                    raise Exception("Account with this email already exists")
                case account_pb.AccountStatus.SUSPENDED:
                    raise Exception("Account with this email is suspended")
                case account_pb.AccountStatus.DELETED:
                    # If the account was deleted, we can allow re-creation
                    if account.api_key:
                        self._api_key_manager.invalidate(account.api_key)
                    account.password = password
                    account.api_key = await self._api_key_manager.generate()
                    account.first_name = first_name
                    account.last_name = last_name
                    account.status = account_pb.AccountStatus.ACTIVE
                    account.last_accessed_at = wkt.Timestamp().now()
                    account.deleted_at = None
                    await self._storage.update(storage_pb.UpdateRequest(
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
                api_key=await self._api_key_manager.generate(),
                first_name=first_name,
                last_name=last_name,
            )
            account.created_at = wkt.Timestamp().now()
            account.last_accessed_at = wkt.Timestamp().now()
            result = await self._storage.insert(storage_pb.InsertRequest(
                subject=Oneof("account", account)
            ))
            account.id = result.id

            # Update metrics
            self._user_signup.increment()
            result = await self._storage.count(storage_pb.CountRequest(
                subject_type=storage_pb.SubjectType.ACCOUNT
            ))
            total_count = result.count
            self._user_total.update(total_count)

            _logger.warning(f"NEW-ACCOUNT: id={account.id}, email={account.email}")

        self._auth_writer.grant(ctx, account.id)

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

        account = await self._find_by_email(email)
        if account is None:
            raise HTTPException(status_code=401, detail="Invalid email or password")
        if password != account.password:
            raise HTTPException(status_code=401, detail="Invalid email or password")
        if account.status != account_pb.AccountStatus.ACTIVE:
            raise HTTPException(status_code=403, detail="Account is not active")

        account.last_accessed_at = wkt.Timestamp().now()
        await self._storage.update(storage_pb.UpdateRequest(
            subject=Oneof("account", account)
        ))

        self._user_login.increment()

        self._auth_writer.grant(ctx, account.id)

        return api_pb.LoginResponse(
            account_id=account.id,
            email=account.email,
            first_name=account.first_name,
            last_name=account.last_name,
        )

    async def get_current_user(
        self, request: api_pb.GetCurrentUserRequest, ctx: RequestContext
    ) -> api_pb.GetCurrentUserResponse:
        account = await account_utils.get_account(self._storage, ctx)
        return api_pb.GetCurrentUserResponse(
            account_id=account.id,
            email=account.email,
            first_name=account.first_name,
            last_name=account.last_name,
        )

    async def refresh_token(
        self, request: api_pb.RefreshTokenRequest, ctx: RequestContext
    ) -> api_pb.RefreshTokenResponse:
        account = await account_utils.get_account(self._storage, ctx)
        self._auth_writer.grant(ctx, account.id)
        return api_pb.RefreshTokenResponse()

    async def get_api_key(
        self, request: api_pb.GetApiKeyRequest, ctx: RequestContext
    ) -> api_pb.GetApiKeyResponse:
        account = await account_utils.get_account(self._storage, ctx)
        if not account.api_key or request.refresh:
            if account.api_key:
                self._api_key_manager.invalidate(account.api_key)
            account.api_key = await self._api_key_manager.generate()
            await self._storage.update(storage_pb.UpdateRequest(
                subject=Oneof("account", account)
            ))
        return api_pb.GetApiKeyResponse(
            api_key=account.api_key
        )

    async def logout(
        self, request: api_pb.LogoutRequest, ctx: RequestContext
    ) -> api_pb.LogoutResponse:
        self._auth_writer.reset(ctx)
        return api_pb.LogoutResponse()

    async def _find_by_email(self, email: str) -> account_pb.Account | None:
        response = await self._storage.list(storage_pb.ListRequest(
            subject_type=storage_pb.SubjectType.ACCOUNT,
            filter=Oneof("account_filter", storage_pb.AccountFilter(email=email))
        ))
        if response.accounts:
            return response.accounts[0]
        return None

