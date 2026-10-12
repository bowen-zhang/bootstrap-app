import dataclasses
import datetime
import protobuf
import secrets

from connectrpc.code import Code
from connectrpc.errors import ConnectError
from connectrpc.request import RequestContext
from protos import account_pb, storage_connect, storage_pb
from third_party.bootstrap_utils import auth_utils


async def get_account(storage_service_client: storage_connect.StorageServiceClient, ctx: RequestContext) -> account_pb.Account:
    account_id = auth_utils.get_account_id(ctx)
    response = await storage_service_client.get(storage_pb.GetRequest(
        id=account_id,
        subject_type=storage_pb.SubjectType.ACCOUNT
    ))
    match response.subject:
        case protobuf.Oneof(field="account", value=val):
            account = val
        case _:
            raise ConnectError(code=Code.UNAUTHENTICATED, message="Account not found")

    if account is None:
        raise ConnectError(code=Code.UNAUTHENTICATED, message="Account not found")
    if account.status != account_pb.AccountStatus.ACTIVE:
        raise ConnectError(code=Code.PERMISSION_DENIED, message="Account is not active")
    return account


class ApiKeyManager:
    @dataclasses.dataclass
    class AccountInfo:
        account_id: str
        expiration: datetime.datetime

    _DEFAULT_EXPIRATION_SECONDS = 5 * 60  # 5 minutes

    _storage_service_client: storage_connect.StorageServiceClient
    _expiration: datetime.timedelta
    _cache: dict[str, AccountInfo]

    def __init__(
            self,
            storage_service_client: storage_connect.StorageServiceClient,
            expiration_sec: int = _DEFAULT_EXPIRATION_SECONDS
        ):
        self._storage_service_client = storage_service_client
        self._expiration = datetime.timedelta(seconds=expiration_sec)
        self._cache = {}

    async def lookup(self, api_key: str) -> str:
        if api_key in self._cache:
            account_info = self._cache[api_key]
            if account_info.expiration > datetime.datetime.now(datetime.timezone.utc):
                return account_info.account_id
            else:
                del self._cache[api_key]

        account_id = await self._lookup_storage(api_key)
        if not account_id:
            raise ConnectError(code=Code.UNAUTHENTICATED, message="API key not found")

        self._cache[api_key] = self.AccountInfo(
            account_id=account_id,
            expiration=datetime.datetime.now(datetime.timezone.utc) + self._expiration
        )
        return account_id

    def invalidate(self, api_key: str) -> None:
        if api_key in self._cache:
            del self._cache[api_key]

    async def generate(self) -> str:
        while True:
            api_key = secrets.token_urlsafe(16)
            account_id = await self._lookup_storage(api_key)
            if account_id is None:
                return api_key

    async def _lookup_storage(self, api_key: str) -> str | None:
        response = await self._storage_service_client.list(storage_pb.ListRequest(
            subject_type=storage_pb.SubjectType.ACCOUNT,
            filter=protobuf.Oneof(field="account_filter", value=storage_pb.AccountFilter(api_key=api_key))
        ))
        if response.accounts:
            return response.accounts[0].id
        else:
            return None
        

