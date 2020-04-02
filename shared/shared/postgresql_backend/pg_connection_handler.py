from typing import Any, Optional

import psycopg2
from psycopg2 import sql
from psycopg2.extras import Json

from shared.di import service_as_singleton
from shared.util import BadCodingError, EnvironmentService, ShutdownService

from .connection_handler import DatabaseError


# TODO: Test this. Add something like a @ensure_connection decorator, that wraps a
# function that uses the database. It should ensure, that a transaction is running
# and if the command fails with psycopg2.InterfaceError (=Connection reset) it should
# be retried. Also it should create a connection, if it wasn't established before.


class ENVIRONMENT_VARIABLES:
    HOST = "DATASTORE_DATABASE_HOST"
    PORT = "DATASTORE_DATABASE_PORT"
    NAME = "DATASTORE_DATABASE_NAME"
    USER = "DATASTORE_DATABASE_USER"
    PASSWORD = "DATASTORE_DATABASE_PASSWORD"


class ConnectionContext:
    def __init__(self, connection_handler):
        self.connection_handler = connection_handler

    def __enter__(self):
        self.connection_handler.connection.__enter__()
        self.connection_handler.set_transaction_running(True)

    def __exit__(self, type, value, traceback):
        self.connection_handler.set_transaction_running(False)
        if self.connection_handler.connection:
            self.connection_handler.connection.__exit__(type, value, traceback)


@service_as_singleton
class PgConnectionHandlerService:

    connection: Optional[Any] = None
    context = None

    environment: EnvironmentService
    shutdown_service: ShutdownService

    def __init__(self, shutdown_service: ShutdownService):
        self.set_transaction_running(False)
        shutdown_service.register(self)

    def set_transaction_running(self, value):
        self.is_transaction_running = value

    def get_connection_params(self):
        return {
            "host": self.environment.get(ENVIRONMENT_VARIABLES.HOST),
            "port": int(self.environment.try_get(ENVIRONMENT_VARIABLES.PORT) or 5432),
            "database": self.environment.get(ENVIRONMENT_VARIABLES.NAME),
            "user": self.environment.get(ENVIRONMENT_VARIABLES.USER),
            "password": self.environment.get(ENVIRONMENT_VARIABLES.PASSWORD),
        }

    def ensure_connection(self):
        if not self.connection:
            try:
                self.connection = psycopg2.connect(**self.get_connection_params())
                self.connection.autocommit = False
            except psycopg2.Error as e:
                self.raise_error(f"Database connection error {e.pgcode}: {e.pgerror}")
        else:
            # TODO: check if alive
            pass

    def get_connection_context(self):
        if self.is_transaction_running:
            raise BadCodingError("You cannot start multiple transactions at once!")

        self.ensure_connection()
        self.context = ConnectionContext(self)
        return self.context

    def to_json(self, data):
        return Json(data)

    def execute(self, query, arguments, sql_parameters=[]):
        connection = self.get_connection_with_open_transaction()
        prepared_query = self.prepare_query(query, sql_parameters)
        with connection.cursor() as cursor:
            cursor.execute(prepared_query, arguments)

    def query(self, query, arguments, sql_parameters=[]):
        connection = self.get_connection_with_open_transaction()
        prepared_query = self.prepare_query(query, sql_parameters)
        with connection.cursor() as cursor:
            cursor.execute(prepared_query, arguments)
            result = cursor.fetchall()
            return result

    def query_single_value(self, query, arguments, sql_parameters=[]):
        connection = self.get_connection_with_open_transaction()
        prepared_query = self.prepare_query(query, sql_parameters)
        with connection.cursor() as cursor:
            cursor.execute(prepared_query, arguments)
            result = cursor.fetchone()

            if result is None:
                return None
            return result[0]

    def query_list_of_single_values(self, query, arguments, sql_parameters=[]):
        result = self.query(query, arguments, sql_parameters)
        return list(map(lambda row: row[0], result))

    def get_connection_with_open_transaction(self) -> Any:
        if not self.connection:
            raise BadCodingError(
                "You should open a db connection first with `get_connection_context()`!"
            )
        if not self.is_transaction_running:
            raise BadCodingError(
                "You should start a transaction with `get_connection_context()`!"
            )
        return self.connection

    def prepare_query(self, query, sql_parameters):
        # TODO: just for demo purposes! Extremely unsafe! remove ASAP!
        class UnsafeSqlLiteral(sql.Composable):
            def __init__(self, string):
                self.string = string

            def as_string(self, *args, **kwargs):
                return self.string

        # the correct way - fails if a json field is accessed
        prepared_query = sql.SQL(query).format(
            *[sql.Identifier(param) for param in sql_parameters]
        )
        # see above!
        # prepared_query = sql.SQL(query).format(
        #     *[UnsafeSqlLiteral(param) for param in sql_parameters]
        # )
        return prepared_query

    def raise_error(self, msg):
        # TODO: log the error!
        raise DatabaseError(msg)

    def shutdown(self):
        if self.connection:
            self.connection.close()
            self.context = None
            self.connection = None
