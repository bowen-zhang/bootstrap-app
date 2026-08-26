from connectrpc_grpcreflect import ServerReflectionASGIApplication, ServerReflectionService
from hypercorn.config import Config
from hypercorn import run
from starlette.applications import Starlette
from starlette.routing import Mount

from protos import storage_connect, storage_pb
from shared.settings import settings, is_dev
from sqlite_storage_service import ProtoSqliteManager, SQLiteStorageService


# 2. Instantiate the base ASGI application with your service
db_manager = ProtoSqliteManager("../../runtime/storage.db")
storage_app = storage_connect.StorageServiceASGIApplication(SQLiteStorageService(db_manager))

reflection_app = ServerReflectionASGIApplication(ServerReflectionService(storage_pb.desc()))

app = Starlette(routes=[
    Mount(storage_app.path, storage_app),
    Mount(reflection_app.path, reflection_app) # Mount reflection at its standard path
])

if __name__ == "__main__":
    config = Config()
    config.bind = [f"127.0.0.1:{settings.storage_service_settings.port}"]
    config.use_reloader = is_dev()
    config.application_path = "main:app" 
    run.run(config)
