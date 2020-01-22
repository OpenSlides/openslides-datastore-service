from .sql_database_backend_service import SqlDatabaseBackendService  # noqa
from .sql_occ_locker_backend_service import SqlOccLockerBackendService  # noqa
from .sql_read_database_backend_service import SqlReadDatabaseBackendService  # noqa


def setup_di():
    from writer.di import injector
    from .connection_handler import ConnectionHandler
    from .pg_connection_handler import PgConnectionHandlerService

    injector.register(ConnectionHandler, PgConnectionHandlerService)
