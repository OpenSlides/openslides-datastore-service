from .sql_database_backend_service import SqlDatabaseBackendService  # noqa
from .sql_occ_locker_backend_service import SqlOccLockerBackendService  # noqa


def setup_di():
    from shared.di import injector
    from shared.postgresql_backend import ConnectionHandler
    from shared.postgresql_backend.pg_connection_handler import (
        PgConnectionHandlerService,
    )

    injector.register(ConnectionHandler, PgConnectionHandlerService)
