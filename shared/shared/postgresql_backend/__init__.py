from .connection_handler import ConnectionHandler
from .sql_event_types import EVENT_TYPES  # noqa
from .sql_query_helper import SqlQueryHelper


def setup_di():
    from shared.di import injector
    from shared.services import ReadDatabase

    from .pg_connection_handler import PgConnectionHandlerService
    from .sql_read_database_backend_service import SqlReadDatabaseBackendService

    injector.register(ConnectionHandler, PgConnectionHandlerService)
    injector.register(SqlQueryHelper, SqlQueryHelper)
    injector.register(ReadDatabase, SqlReadDatabaseBackendService)
