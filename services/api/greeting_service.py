import datetime
import logging
import protobuf
import protobuf.wkt

from connectrpc.request import RequestContext

from protos import api_connect, api_pb, storage_pb,user_data_pb
from services.api.auth_interceptor import get_account


logger = logging.getLogger(__name__)


class GreetingService(api_connect.GreetingService):
    def __init__(self, storage_service_client):
        self._storage = storage_service_client

    async def greet(
        self, request: api_pb.GreetRequest, ctx: RequestContext
    ) -> api_pb.GreetResponse:
        try:
            account = get_account(self._storage, ctx)

            self._storage.insert(storage_pb.InsertRequest(
                subject=protobuf.Oneof(
                    field="user_data", 
                    value=user_data_pb.UserData(
                        user_id=account.id,
                        accessed_at=protobuf.wkt.Timestamp.from_datetime(
                            datetime.datetime.now(datetime.timezone.utc)
                        )
                    )
                )
            ))

            all_user_data = self._storage.list(storage_pb.ListRequest(
                subject_type=storage_pb.SubjectType.USER_DATA,
                user_id=account.id,
            )).user_data
            print(all_user_data)

            return api_pb.GreetResponse(
                message=f"Hello, {account.first_name}!",
                user_data=all_user_data
            )
        except Exception as e:
            logger.error(f"{e}", exc_info=True)
            raise
