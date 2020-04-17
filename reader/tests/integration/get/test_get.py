from unittest.mock import MagicMock

import pytest

from reader.core import Reader
from reader.core.reader_service import ReaderService
from reader.flask_frontend.json_handler import JSONHandler
from reader.flask_frontend.routes import Route
from shared.core import ReadDatabase
from shared.di import injector
from shared.postgresql_backend import ConnectionHandler
from shared.postgresql_backend.sql_read_database_backend_service import (
    SqlReadDatabaseBackendService,
)
from shared.tests import reset_di  # noqa


class FakeConnectionHandler:
    def get_connection_context(self):
        return MagicMock()


@pytest.fixture(autouse=True)
def setup_di(reset_di):  # noqa
    injector.register_as_singleton(ConnectionHandler, FakeConnectionHandler)
    injector.register_as_singleton(ReadDatabase, SqlReadDatabaseBackendService)
    injector.register_as_singleton(Reader, ReaderService)


@pytest.fixture()
def json_handler():
    yield JSONHandler()


@pytest.fixture()
def connection():
    yield injector.get(ConnectionHandler)


def test_simple(json_handler: JSONHandler, connection: ConnectionHandler):
    model = MagicMock()

    def query(query, arguments, sql_params=[]):
        if "from models_lookup" in query:
            return [{"fqid": fqid, "deleted": False} for fqid in arguments[0]]
        if "from models" in query:
            return [{"fqid": fqid, "data": model} for fqid in arguments[0]]

    connection.query = query

    request = {"fqid": "fqid"}
    result = json_handler.handle_request(Route.GET, request)
    assert result == model
