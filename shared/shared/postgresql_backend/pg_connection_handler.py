import threading
from threading import Semaphore

import psycopg2
from psycopg2 import sql
from psycopg2.extras import DictCursor, Json
from psycopg2.pool import ThreadedConnectionPool

from shared.di import service_as_singleton
from shared.services import EnvironmentService, ShutdownService
from shared.util import BadCodingError, logger

from .connection_handler import DatabaseError


# TODO: Test this. Add something like a @ensure_connection decorator, that wraps a
# function that uses the database. It should ensure, that a transaction is running
# and if the command fails with psycopg2.InterfaceError (=Connection reset) it should
# be retried. Also it should create a connection, if it wasn't established before.


class DATABASE_ENVIRONMENT_VARIABLES:
    HOST = "DATASTORE_DATABASE_HOST"
    PORT = "DATASTORE_DATABASE_PORT"
    NAME = "DATASTORE_DATABASE_NAME"
    USER = "DATASTORE_DATABASE_USER"
    PASSWORD = "DATASTORE_DATABASE_PASSWORD"


class ConnectionContext:
    def __init__(self, connection_handler):
        self.connection_handler = connection_handler

    def __enter__(self):
        self.connection = self.connection_handler.get_connection()
        self.connection.__enter__()

    def __exit__(self, exception, exception_value, traceback):
        has_connection_error = exception is not None and issubclass(
            exception, psycopg2.Error
        )
        if has_connection_error:
            # make sure the connection was already closed by psycopg
            assert self.connection.closed > 0
        else:
            self.connection.__exit__(exception, exception_value, traceback)
        self.connection_handler.put_connection(self.connection, has_connection_error)

        if has_connection_error:
            self.connection_handler.raise_error(
                f"Database connection error ({exception.__name__}, code {exception_value.pgcode}): {exception_value.pgerror}"  # noqa
            )


@service_as_singleton
class PgConnectionHandlerService:

    _storage: threading.local
    connection_pool: ThreadedConnectionPool

    environment: EnvironmentService
    shutdown_service: ShutdownService

    def __init__(self, shutdown_service: ShutdownService):
        shutdown_service.register(self)
        self._storage = threading.local()

        min_conn = int(self.environment.try_get("DATASTORE_MIN_CONNECTIONS") or 1)
        max_conn = int(self.environment.try_get("DATASTORE_MAX_CONNECTIONS") or 1)
        self._semaphore = Semaphore(max_conn)
        try:
            self.connection_pool = ThreadedConnectionPool(
                min_conn, max_conn, **self.get_connection_params()
            )
        except psycopg2.Error as e:
            self.raise_error(
                f"Database connection error ({type(e).__name__}) {e.pgcode}: {e.pgerror}"  # noqa
            )

    def get_current_connection(self):
        try:
            return self._storage.connection
        except AttributeError:
            return None

    def set_current_connection(self, connection):
        self._storage.connection = connection

    def get_connection_params(self):
        return {
            "host": self.environment.get(DATABASE_ENVIRONMENT_VARIABLES.HOST),
            "port": int(
                self.environment.try_get(DATABASE_ENVIRONMENT_VARIABLES.PORT) or 5432
            ),
            "database": self.environment.get(DATABASE_ENVIRONMENT_VARIABLES.NAME),
            "user": self.environment.get(DATABASE_ENVIRONMENT_VARIABLES.USER),
            "password": self.environment.get(DATABASE_ENVIRONMENT_VARIABLES.PASSWORD),
            "cursor_factory": DictCursor,
        }

    def get_connection(self):
        if old_conn := self.get_current_connection():
            if old_conn.closed:
                # If an error happens while returning the connection to the pool, it
                # might still be set as the current connection although it is already
                # closed. In this case, we just discard it.
                logger.debug(f"Discarding old connection (closed={old_conn.closed})")
                logger.debug("This indicates a previous error, please check the logs")
                self.put_connection(old_conn, True)
            else:
                raise BadCodingError(
                    "You cannot start multiple transactions in one thread!"
                )
        self._semaphore.acquire()
        connection = self.connection_pool.getconn()
        connection.autocommit = False
        self.set_current_connection(connection)
        return connection

    def put_connection(self, connection, has_error):
        """
        has_error indicated, whether to not reuse the connection.
        If the connection encountered an error, set it to true, so
        it will be discarded from the pool.
        """
        if connection != self.get_current_connection():
            raise BadCodingError("Invalid connection")

        self.connection_pool.putconn(connection, close=has_error)
        self.set_current_connection(None)
        self._semaphore.release()

    def get_connection_context(self):
        return ConnectionContext(self)

    def to_json(self, data):
        return Json(data)

    def execute(self, query, arguments, sql_parameters=[]):
        prepared_query = self.prepare_query(query, sql_parameters)
        with self.get_current_connection().cursor() as cursor:
            cursor.execute(prepared_query, arguments)

    def query(self, query, arguments, sql_parameters=[]):
        prepared_query = self.prepare_query(query, sql_parameters)
        with self.get_current_connection().cursor() as cursor:
            cursor.execute(prepared_query, arguments)
            result = cursor.fetchall()
            return result

    def query_single_value(self, query, arguments, sql_parameters=[]):
        prepared_query = self.prepare_query(query, sql_parameters)
        with self.get_current_connection().cursor() as cursor:
            cursor.execute(prepared_query, arguments)
            result = cursor.fetchone()

            if result is None:
                return None
            return result[0]

    def query_list_of_single_values(self, query, arguments, sql_parameters=[]):
        result = self.query(query, arguments, sql_parameters)
        return list(map(lambda row: row[0], result))

    def prepare_query(self, query, sql_parameters):
        prepared_query = sql.SQL(query).format(
            *[sql.Identifier(param) for param in sql_parameters]
        )
        return prepared_query

    def raise_error(self, msg):
        logger.error(f"Connection handler error: {msg}")
        raise DatabaseError(msg)

    def shutdown(self):
        self.connection_pool.closeall()
