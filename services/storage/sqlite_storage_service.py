from __future__ import annotations

import uuid
from pathlib import Path
from protobuf import Oneof
from typing import Any

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Connection
from sqlalchemy.pool import StaticPool

from protos import account_pb, storage_connect, storage_pb


class ProtoSqliteTable:
    def __init__(self, connection: Connection, table_name: str, subject_type: int, subject_class: type):
        self._connection = connection
        self._table_name = table_name
        self._subject_type = subject_type
        self._subject_class = subject_class

    @property
    def table_name(self) -> str:
        return self._table_name

    @property
    def subject_type(self) -> int:
        return self._subject_type

    @property
    def subject_class(self) -> type:
        return self._subject_class

    def execute(self, query: str, params: dict[str, Any] | None = None):
        return self._connection.execute(text(query), params or {})

    def commit(self):
        self._connection.commit()

    def create(self):
        self.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {self._table_name} (
                id TEXT PRIMARY KEY,
                data TEXT NOT NULL,

                CONSTRAINT valid_json CHECK (json_valid(data))
            )
            """
        )
        self.commit()

    def save(self, subject: Any) -> None:
        if not isinstance(subject, self._subject_class):
            raise ValueError(f"Expected subject of type {self._subject_class.__name__}, got {type(subject).__name__}")

        self._connection.execute(
            text(f"INSERT OR REPLACE INTO {self._table_name} (id, data) VALUES (:id, :data)"),
            {"id": subject.id, "data": subject.to_json()},
        )
        self._connection.commit()

    def get(self, subject_id: str) -> Any | None:
        row = self._connection.execute(
            text(f"SELECT id, data FROM {self._table_name} WHERE id = :subject_id"),
            {"subject_id": subject_id},
        ).fetchone()
        if row is None:
            return None
        return self._deserialize_subject(row.id, row.data)

    def list(self, filter_clause: str | None = None, filter_params: dict[str, Any] | None = None) -> list[Any]:
        rows = self._connection.execute(
            text(f"SELECT id, data FROM {self._table_name}" + (f" WHERE {filter_clause}" if filter_clause else "") + " ORDER BY id"),
            filter_params or {}
        ).fetchall()
        for row in rows:
            yield self._deserialize_subject(row.id, row.data)

    def delete(self, id: str) -> None:
        self._connection.execute(
            text(f"DELETE FROM {self._table_name} WHERE id = :subject_id"),
            {"subject_id": id},
        )
        self._connection.commit()

    def delete_all(self) -> int:
        result = self._connection.execute(text(f"DELETE FROM {self._table_name}"))
        self._connection.commit()
        return result.rowcount

    def _deserialize_subject(self, id: str, data: str) -> Any:
        subject_cls = self._subject_class()
        subject = subject_cls.from_json(data)        
        subject.id = id
        return subject


class ProtoSqliteDatabase:
    def __init__(self, connection: Connection):
        self._connection = connection
        self._account_table = ProtoSqliteTable(connection, "account", storage_pb.SubjectType.ACCOUNT, account_pb.Account)

        self._tables = [
            self._account_table,
        ]
        self._tables_by_class = {t.subject_class: t for t in self._tables}
        self._tables_by_type = {t.subject_type: t for t in self._tables}

    @property
    def tables(self) -> list[ProtoSqliteTable]:
        return self._tables

    @property
    def account_table(self) -> ProtoSqliteTable:
        return self._account_table

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self._connection.close()

    def get_table_by_subject(self, subject: Any) -> ProtoSqliteTable:
        cls = type(subject)
        if cls not in self._tables_by_class:
            raise ValueError(f'Table not found for {cls.__name__}')

        return self._tables_by_class[cls]

    def get_table_by_subject_type(self, subject_type: int) -> ProtoSqliteTable:
        if subject_type not in self._tables_by_type:
            raise ValueError(f'Table not found for subject type {subject_type}')
        
        return self._tables_by_type[subject_type]


class ProtoSqliteManager:
    def __init__(self, database_path: str = "storage.db"):
        db_file = Path(database_path)
        db_file.parent.mkdir(parents=True, exist_ok=True)

        self._engine = create_engine(
            f"sqlite:///{db_file}",
            poolclass=StaticPool,
            connect_args={"check_same_thread": False},
        )

    def close(self):
        self._engine.dispose()

    def get_database(self):
        return ProtoSqliteDatabase(self._engine.connect())


class SQLiteStorageService(storage_connect.StorageService):
    def __init__(self, db_manager: ProtoSqliteManager):
        self._db_manager = db_manager
        self.engine = self._db_manager._engine
        self._ensure_schema()

    def _ensure_schema(self) -> None:
        with self._db_manager.get_database() as db:
            for table in db.tables:
                table.create()

    def close(self) -> None:
        self._db_manager.close()

    async def insert(self, request: storage_pb.InsertRequest, ctx: Any) -> storage_pb.InsertResponse:
        with self._db_manager.get_database() as db:
            subject = self._get_subject(request)
            if subject.id:
                raise ValueError('Unable to insert data with pre-existing id.')
            subject.id = str(uuid.uuid4())

            table = db.get_table_by_subject(subject)
            table.save(subject)
            return storage_pb.InsertResponse(id=subject.id)

    async def get(self, request: storage_pb.GetRequest, ctx: Any) -> storage_pb.GetResponse:
        with self._db_manager.get_database() as db:
            table = db.get_table_by_subject_type(request.subject_type)
            subject = table.get(request.id)

            response = storage_pb.GetResponse()
            if subject:
                if request.subject_type == storage_pb.SubjectType.ACCOUNT:
                    response.subject = Oneof(field="account", value=subject)

            return response

    async def list(self, request: storage_pb.ListRequest, ctx: Any) -> storage_pb.ListResponse:
        with self._db_manager.get_database() as db:
            table = db.get_table_by_subject_type(request.subject_type)

            response = storage_pb.ListResponse()
            if request.subject_type == storage_pb.SubjectType.ACCOUNT:
                if request.filter.value:
                    filter_clause = "email = :email"
                    filter_params = {"email": request.filter.value.email}
                else:
                    filter_clause = None
                    filter_params = None
                response.accounts = list(table.list(filter_clause=filter_clause, filter_params=filter_params))

            return response

    async def update(self, request: storage_pb.UpdateRequest, ctx: Any) -> storage_pb.UpdateResponse:
        with self._db_manager.get_database() as db:
            subject = self._get_subject(request)
            if not subject.id:
                raise ValueError('Unable to update data without id.')

            table = db.get_table_by_subject(subject)
            table.save(subject)

            return storage_pb.UpdateResponse()

    async def delete(self, request: storage_pb.DeleteRequest, ctx: Any) -> storage_pb.DeleteResponse:
        with self._db_manager.get_database() as db:
            table = db.get_table_by_subject_type(request.subject_type)
            table.delete(request.id)
            return storage_pb.DeleteResponse()

    async def delete_all(self, request: storage_pb.DeleteAllRequest, ctx: Any) -> storage_pb.DeleteAllResponse:
        with self._db_manager.get_database() as db:
            table = db.get_table_by_subject_type(request.subject_type)
            count = table.delete_all()
            
            return storage_pb.DeleteAllResponse(deleted_count=count)

    @staticmethod
    def _get_subject(request: Any) -> Any:
        return request.subject.value
