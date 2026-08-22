from __future__ import annotations

from typing import Any

from protos import storage_connect, storage_pb2


class MongoStorageService(storage_connect.StorageService):
    """Placeholder implementation for MongoDB-backed storage.

    This service follows the same StorageService RPC contract as the SQLite
    implementation, but the actual database interaction is intentionally left
    unimplemented for now.
    """

    def __init__(self, uri: str = "mongodb://localhost:27017", database_name: str = "bootstrap_app"):
        self.uri = uri
        self.database_name = database_name

    async def insert(self, request: storage_pb2.InsertRequest, ctx: Any) -> storage_pb2.InsertResponse:
        raise NotImplementedError("MongoDB storage is not implemented yet")

    async def get(self, request: storage_pb2.GetRequest, ctx: Any) -> storage_pb2.GetResponse:
        raise NotImplementedError("MongoDB storage is not implemented yet")

    async def list(self, request: storage_pb2.ListRequest, ctx: Any) -> storage_pb2.ListResponse:
        raise NotImplementedError("MongoDB storage is not implemented yet")

    async def update(self, request: storage_pb2.UpdateRequest, ctx: Any) -> storage_pb2.UpdateResponse:
        raise NotImplementedError("MongoDB storage is not implemented yet")

    async def delete(self, request: storage_pb2.DeleteRequest, ctx: Any) -> storage_pb2.DeleteResponse:
        raise NotImplementedError("MongoDB storage is not implemented yet")

    async def delete_all(self, request: storage_pb2.DeleteAllRequest, ctx: Any) -> storage_pb2.DeleteAllResponse:
        raise NotImplementedError("MongoDB storage is not implemented yet")
