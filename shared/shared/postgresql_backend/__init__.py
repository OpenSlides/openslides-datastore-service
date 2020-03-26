from .connection_handler import ConnectionHandler  # noqa
from .sql_event_types import EVENT_TYPES  # noqa


def setup_di():
    from shared.di import injector
    from .sql_read_database_backend_service import SqlReadDatabaseBackendService
    from shared.core import ReadDatabase
    from .pg_connection_handler import PgConnectionHandlerService

    injector.register(ConnectionHandler, PgConnectionHandlerService)
    injector.register(ReadDatabase, SqlReadDatabaseBackendService)
