import pytest

from reader.core.reader_service import ReaderService
from reader.core.requests import GetRequest
from shared.di import injector
from shared.core import DeletedModelsBehaviour, ReadDatabase
from unittest.mock import MagicMock
from reader.core import Reader
from shared.postgresql_backend import ConnectionHandler
from shared.tests import reset_di  # noqa


@pytest.fixture(autouse=True)
def provide_di(reset_di):  # noqa
    injector.register_as_singleton(ConnectionHandler, MagicMock)
    injector.register_as_singleton(ReadDatabase, MagicMock)
    injector.register(Reader, ReaderService)
    yield


@pytest.fixture()
def reader(provide_di):
    yield injector.get(Reader)


@pytest.fixture()
def read_db(provide_di):
    yield injector.get(ReadDatabase)


def test_get(reader, read_db):
    model = MagicMock()
    read_db.get = MagicMock(return_value=model)
    read_db.is_deleted = MagicMock(return_value=False)

    request = GetRequest("fqid", ["field"])
    reader.get(request)

    read_db.get_context.assert_called()
    read_db.get.assert_called_with("fqid", ["field"])
