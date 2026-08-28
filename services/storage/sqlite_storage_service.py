from __future__ import annotations

import uuid
from pathlib import Path
from protobuf import Oneof
from typing import Any

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Connection
from sqlalchemy.pool import StaticPool

from protos import account_pb, storage_connect, storage_pb, user_data_pb


_NON_USER_DATA_CLASSES = [account_pb.Account]


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

    def get(self, id: str) -> Any | None:
        return self.find_one(filter_clause="id = :subject_id", filter_params={"subject_id": id})

    def find_one(self, filter_clause: str | None = None, filter_params: dict[str, Any] | None = None) -> Any | None:
        row = self._connection.execute(
            text(f"SELECT id, data FROM {self._table_name}" + (f" WHERE {filter_clause}" if filter_clause else "") + " LIMIT 1"),
            filter_params or {},
        ).fetchone()
        if row is None:
            return None
        return self._deserialize_subject(row.id, row.data)

    def find_all(self, filter_clause: str | None = None, filter_params: dict[str, Any] | None = None):
        rows = self._connection.execute(
            text(f"SELECT id, data FROM {self._table_name}" + (f" WHERE {filter_clause}" if filter_clause else "") + " ORDER BY id"),
            filter_params or {}
        ).fetchall()
        for row in rows:
            yield self._deserialize_subject(row.id, row.data)

    def delete(self, filter_clause: str | None = None, filter_params: dict[str, Any] | None = None) -> None:
        result = self._connection.execute(
            text(f"DELETE FROM {self._table_name}" + (f" WHERE {filter_clause}" if filter_clause else "")),
            filter_params or {},
        )
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

        self._tables = [
            ProtoSqliteTable(connection, "account", storage_pb.SubjectType.ACCOUNT, account_pb.Account),
            ProtoSqliteTable(connection, "userData", storage_pb.SubjectType.USER_DATA, user_data_pb.UserData)
        ]
        self._tables_by_class = {t.subject_class: t for t in self._tables}
        self._tables_by_type = {t.subject_type: t for t in self._tables}

    @property
    def tables(self) -> list[ProtoSqliteTable]:
        return self._tables

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
            if self._is_user_data(subject) and not subject.user_id:
                raise ValueError('Unable to insert user data without user_id.')

            subject.id = str(uuid.uuid4())

            table = db.get_table_by_subject(subject)
            table.save(subject)
            return storage_pb.InsertResponse(id=subject.id)

    async def get(self, request: storage_pb.GetRequest, ctx: Any) -> storage_pb.GetResponse:
        if not request.subject_type:
            raise ValueError('Unable to get data. Subject type is missing.')
        if not request.id:
            raise ValueError('Unable to get data. Subject id is missing.')

        with self._db_manager.get_database() as db:
            table = db.get_table_by_subject_type(request.subject_type)
            filter_clauses = ["id = :subject_id"]
            filter_params={"subject_id": request.id}

            if self._is_user_data_type(table.subject_class):
                if not request.user_id:
                    raise ValueError('Unable to get data. User id is missing.')
                filter_clauses.append("data->>'$.userId' = :user_id")
                filter_params["user_id"] = request.user_id
            
            subject = table.find_one(filter_clause=" AND ".join(filter_clauses), filter_params=filter_params)

            response = storage_pb.GetResponse()
            if subject:
                if request.subject_type == storage_pb.SubjectType.ACCOUNT:
                    response.subject = Oneof(field="account", value=subject)

            return response

    async def list(self, request: storage_pb.ListRequest, ctx: Any) -> storage_pb.ListResponse:
        if not request.subject_type:
            raise ValueError('Unable to list data. Subject type is missing.')

        with self._db_manager.get_database() as db:
            table = db.get_table_by_subject_type(request.subject_type)

            filter_clauses = []
            filter_params = {}

            if self._is_user_data_type(table.subject_class):
                if not request.user_id:
                    raise ValueError('Unable to list data. User id is missing.')
                filter_clauses.append("data->>'$.userId' = :user_id")
                filter_params["user_id"] = request.user_id

            if request.subject_type == storage_pb.SubjectType.ACCOUNT:
                if request.filter.value:
                    filter_clauses.append("data->>'$.email' = :email")
                    filter_params["email"] = request.filter.value.email

            data = list(table.find_all(filter_clause=" AND ".join(filter_clauses), filter_params=filter_params))

            response = storage_pb.ListResponse()
            if request.subject_type == storage_pb.SubjectType.ACCOUNT:
                response.account = data
            elif request.subject_type == storage_pb.SubjectType.USER_DATA:
                response.user_data = data
            return response

    async def update(self, request: storage_pb.UpdateRequest, ctx: Any) -> storage_pb.UpdateResponse:
        with self._db_manager.get_database() as db:
            subject = self._get_subject(request)
            if not subject.id:
                raise ValueError('Unable to update data without id.')

            table = db.get_table_by_subject(subject)

            filter_clauses = ["id = :subject_id"]
            filter_params={"subject_id": subject.id}

            if self._is_user_data(subject):
                if not subject.user_id:
                    raise ValueError('Unable to update data. User id is missing.')
                filter_clauses.append("data->>'$.userId' = :user_id")
                filter_params["user_id"] = subject.user_id
            
            subject = table.find_one(filter_clause=" AND ".join(filter_clauses), filter_params=filter_params)
            if not subject:
                raise ValueError('Unable to update data. Subject not found.')

            table.save(subject)

            return storage_pb.UpdateResponse()

    async def delete(self, request: storage_pb.DeleteRequest, ctx: Any) -> storage_pb.DeleteResponse:
        if not request.subject_type:
            raise ValueError('Unable to delete data. Subject type is missing.')
        if not request.id:
            raise ValueError('Unable to delete data. Subject id is missing.')

        with self._db_manager.get_database() as db:
            table = db.get_table_by_subject_type(request.subject_type)

            filter_clauses = ["id = :subject_id"]
            filter_params={"subject_id": request.id}

            if self._is_user_data_type(table.subject_class):
                if not request.user_id:
                    raise ValueError('Unable to delete data. User id is missing.')
                filter_clauses.append("data->>'$.userId' = :user_id")
                filter_params["user_id"] = request.user_id

            count = table.delete(filter_clause=" AND ".join(filter_clauses), filter_params=filter_params)
            return storage_pb.DeleteResponse(deleted_count=count)

    async def delete_all(self, request: storage_pb.DeleteAllRequest, ctx: Any) -> storage_pb.DeleteAllResponse:
        if not request.subject_type:
            raise ValueError('Unable to delete all data. Subject type is missing.')

        with self._db_manager.get_database() as db:
            table = db.get_table_by_subject_type(request.subject_type)

            filter_clauses = []
            filter_params = {}
            if self._is_user_data_type(table.subject_class):
                if not request.user_id:
                    raise ValueError('Unable to delete all data. User id is missing.')
                filter_clauses.append("data->>'$.userId' = :user_id")
                filter_params["user_id"] = request.user_id

            count = table.delete(filter_clause=" AND ".join(filter_clauses), filter_params=filter_params)
            return storage_pb.DeleteAllResponse(deleted_count=count)

    @staticmethod
    def _get_subject(request: Any) -> Any:
        return request.subject.value

    @staticmethod
    def _is_user_data(subject: Any) -> bool:
        return type(subject) not in _NON_USER_DATA_CLASSES

    @staticmethod
    def _is_user_data_type(subject_class: type) -> bool:
        return subject_class not in _NON_USER_DATA_CLASSES