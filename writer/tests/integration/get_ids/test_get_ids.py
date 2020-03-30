from unittest.mock import MagicMock

import pytest

from shared.di import injector
from shared.flask_frontend import InvalidRequest
from shared.postgresql_backend import ConnectionHandler
from shared.services import ReadDatabase
from shared.tests import reset_di  # noqa
from shared.util import InvalidFormat
from writer.core import Database, Messaging, OccLocker, setup_di as core_setup_di
from writer.flask_frontend.json_handlers import GetIdsHandler
from writer.postgresql_backend import SqlDatabaseBackendService
from writer.postgresql_backend.sql_database_backend_service import COLLECTION_MAX_LEN


class FakeConnectionHandler:
    # We do just need the following three methods from the connection handler

    def __init__(self):
        self.storage = {}

    def get_connection_context(self):
        return MagicMock()

    def execute(self, statement, arguments):
        collection = arguments[0]
        id = arguments[1]
        self.storage[collection] = id

    def query_single_value(self, query, arguments):
        collection = arguments[0]
        return self.storage.get(collection)


@pytest.fixture(autouse=True)
def setup_di(reset_di):  # noqa
    injector.register_as_singleton(ConnectionHandler, FakeConnectionHandler)
    injector.register_as_singleton(ReadDatabase, MagicMock)
    injector.register(Database, SqlDatabaseBackendService)
    injector.register_as_singleton(OccLocker, MagicMock)
    injector.register_as_singleton(Messaging, MagicMock)
    core_setup_di()


@pytest.fixture()
def get_ids_handler():
    yield GetIdsHandler()


@pytest.fixture()
def connection_handler():
    yield injector.get(ConnectionHandler)


def test_simple(get_ids_handler, connection_handler):
    ids = get_ids_handler.get_ids({"amount": 1, "collection": "test_collection"})

    assert ids == [1]
    assert connection_handler.storage.get("test_collection") == 2


def test_wrong_format(get_ids_handler):
    with pytest.raises(InvalidRequest):
        get_ids_handler.get_ids({"unknown_field": "some value"})


def test_negative_amount(get_ids_handler, connection_handler):
    with pytest.raises(InvalidFormat):
        get_ids_handler.get_ids({"amount": -1, "collection": "test_collection"})


def test_too_long_collection(get_ids_handler, connection_handler):
    with pytest.raises(InvalidFormat):
        get_ids_handler.get_ids(
            {"amount": 1, "collection": "x" * (COLLECTION_MAX_LEN + 1)}
        )


def test_multiple_ids(get_ids_handler, connection_handler):
    ids = get_ids_handler.get_ids({"amount": 4, "collection": "test_collection"})

    assert ids == [1, 2, 3, 4]
    assert connection_handler.storage.get("test_collection") == 5


def test_successive_collections(get_ids_handler, connection_handler):
    get_ids_handler.get_ids({"amount": 2, "collection": "test_collection1"})
    ids = get_ids_handler.get_ids({"amount": 3, "collection": "test_collection2"})

    assert ids == [1, 2, 3]
    assert connection_handler.storage.get("test_collection2") == 4


def test_successive_ids(get_ids_handler, connection_handler):
    get_ids_handler.get_ids({"amount": 2, "collection": "test_collection"})
    ids = get_ids_handler.get_ids({"amount": 3, "collection": "test_collection"})

    assert ids == [3, 4, 5]
    assert connection_handler.storage.get("test_collection") == 6
