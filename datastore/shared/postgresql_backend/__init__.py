from .connection_handler import ConnectionHandler, DatabaseError  # noqa
from .pg_connection_handler import retry_on_db_failure  # noqa
from .sql_event_types import EVENT_TYPES  # noqa
from .sql_query_helper import SqlQueryHelper


def setup_di():
    from datastore.shared.di import injector
    from datastore.shared.services import ReadDatabase

    from .pg_connection_handler import PgConnectionHandlerService
    from .sql_read_database_backend_service import SqlReadDatabaseBackendService

    injector.register(ConnectionHandler, PgConnectionHandlerService)
    injector.register(SqlQueryHelper, SqlQueryHelper)
    injector.register(ReadDatabase, SqlReadDatabaseBackendService)
