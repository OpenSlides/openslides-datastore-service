import threading
from functools import wraps
from threading import Semaphore
from time import sleep

import psycopg2
from psycopg2 import sql
from psycopg2.extras import DictCursor, Json, execute_values
from psycopg2.pool import ThreadedConnectionPool

from datastore.shared.di import injector, service_as_singleton
from datastore.shared.services import EnvironmentService, ShutdownService
from datastore.shared.util import BadCodingError, logger

from .connection_handler import DatabaseError


def retry_on_db_failure(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        env_service: EnvironmentService = injector.get(EnvironmentService)
        RETRY_TIMEOUT = int(env_service.try_get("DATASTORE_RETRY_TIMEOUT") or 10)
        MAX_RETRIES = int(env_service.try_get("DATASTORE_MAX_RETRIES") or 3)
        tries = 0
        while True:
            try:
                return fn(*args, **kwargs)
            except DatabaseError as e:
                # this seems to be the only indication for a sudden connection break
                if (
                    isinstance(e.base_exception, psycopg2.OperationalError)
                    and e.base_exception.pgcode is None
                ):
                    tries += 1
                    if tries < MAX_RETRIES:
                        oe = e.base_exception
                        logger.info(
                            f"Retrying request to database because of the following error ({type(oe).__name__}, code {oe.pgcode}): {oe.pgerror}"  # noqa
                        )
                    else:
                        raise
                else:
                    raise
            if RETRY_TIMEOUT:
                sleep(RETRY_TIMEOUT / 1000)

    return wrapper


class DATABASE_ENVIRONMENT_VARIABLES:
    HOST = "DATASTORE_DATABASE_HOST"
    PORT = "DATASTORE_DATABASE_PORT"
    NAME = "DATASTORE_DATABASE_NAME"
    USER = "DATASTORE_DATABASE_USER"
    PASSWORD_FILE = "DATASTORE_DATABASE_PASSWORD_FILE"


EXECUTE_VALUES_PAGE_SIZE = int(1e7)


class ConnectionContext:
    def __init__(self, connection_handler):
        self.connection_handler = connection_handler

    def __enter__(self):
        try:
            self.connection_handler._semaphore.acquire()
            self.connection = self.connection_handler.get_connection()
            self.connection.__enter__()
        except:
            raise
        finally:
            self.connection_handler._semaphore.release()

    def __exit__(self, exception, exception_value, traceback):
        try:
            self.connection_handler._semaphore.acquire()
            has_connection_error = exception is not None and issubclass(
                exception, psycopg2.Error
            )
            if has_connection_error:
                # make sure the connection was already closed by psycopg
                assert self.connection.closed > 0
            else:
                self.connection.__exit__(exception, exception_value, traceback)
            self.connection_handler.put_connection(
                self.connection, has_connection_error
            )

            if has_connection_error:
                self.connection_handler.raise_error(exception_value)
        except:
            raise
        finally:
            self.connection_handler._semaphore.release()


@service_as_singleton
class PgConnectionHandlerService:

    _storage: threading.local
    connection_pool: ThreadedConnectionPool

    environment: EnvironmentService
    shutdown_service: ShutdownService

    def __init__(self, shutdown_service: ShutdownService):
        shutdown_service.register(self)
        self._storage = threading.local()

        min_conn = int(self.environment.try_get("DATASTORE_MIN_CONNECTIONS") or 0)
        max_conn = int(self.environment.try_get("DATASTORE_MAX_CONNECTIONS") or 1)
        self._semaphore = Semaphore()
        try:
            self.connection_pool = ThreadedConnectionPool(
                min_conn, max_conn, **self.get_connection_params()
            )
        except psycopg2.Error as e:
            self.raise_error(e)

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
            "password": self.environment.get_from_file(
                DATABASE_ENVIRONMENT_VARIABLES.PASSWORD_FILE
            ),
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

    def get_connection_context(self):
        return ConnectionContext(self)

    def to_json(self, data):
        return Json(data)

    def execute(self, query, arguments, sql_parameters=[], use_execute_values=False):
        prepared_query = self.prepare_query(query, sql_parameters)
        with self.get_current_connection().cursor() as cursor:
            if use_execute_values:
                execute_values(
                    cursor,
                    prepared_query,
                    arguments,
                    page_size=EXECUTE_VALUES_PAGE_SIZE,
                )
            else:
                cursor.execute(prepared_query, arguments)

    def query(self, query, arguments, sql_parameters=[], use_execute_values=False):
        prepared_query = self.prepare_query(query, sql_parameters)
        with self.get_current_connection().cursor() as cursor:
            if use_execute_values:
                result = execute_values(
                    cursor,
                    prepared_query,
                    arguments,
                    page_size=EXECUTE_VALUES_PAGE_SIZE,
                    fetch=True,
                )
            else:
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

    def query_list_of_single_values(
        self, query, arguments, sql_parameters=[], use_execute_values=False
    ):
        result = self.query(query, arguments, sql_parameters, use_execute_values)
        return list(map(lambda row: row[0], result))

    def prepare_query(self, query, sql_parameters):
        prepared_query = sql.SQL(query).format(
            *[sql.Identifier(param) for param in sql_parameters]
        )
        return prepared_query

    def raise_error(self, e: psycopg2.Error):
        msg = f"Database connection error ({type(e).__name__}, code {e.pgcode}): {e.pgerror}"  # noqa
        logger.error(msg)
        raise DatabaseError(msg, e)

    def shutdown(self):
        self.connection_pool.closeall()
