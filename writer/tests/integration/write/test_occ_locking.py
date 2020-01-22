import copy
from unittest.mock import MagicMock

import pytest

from tests.reset_di import reset_di  # noqa
from writer.core import (
    Database,
    Messaging,
    ModelLocked,
    OccLocker,
    ReadDatabase,
    setup_di as core_setup_di,
)
from writer.di import injector
from writer.flask_frontend.json_handlers import WriteHandler
from writer.postgresql_backend import SqlOccLockerBackendService
from writer.postgresql_backend.connection_handler import ConnectionHandler


class FakeConnectionHandler:
    def query_single_value(self, query, arguments):
        if "jsonb" in query:
            return self.fqfield()
        elif "fqid" in query:
            return self.fqid()
        elif "collectionfield":
            return self.collectionfield()

    def fqid(self):
        ""

    def fqfield(self):
        ""

    def collectionfield(self):
        ""


@pytest.fixture(autouse=True)
def setup_di(reset_di):  # noqa
    injector.register_as_singleton(ConnectionHandler, FakeConnectionHandler)
    injector.register(OccLocker, SqlOccLockerBackendService)
    injector.register_as_singleton(Database, MagicMock)
    injector.register_as_singleton(ReadDatabase, MagicMock)
    injector.register_as_singleton(Messaging, MagicMock)
    core_setup_di()


@pytest.fixture()
def write_handler():
    yield WriteHandler()


@pytest.fixture()
def connection_handler():
    yield injector.get(ConnectionHandler)


@pytest.fixture()
def valid_metadata():
    yield copy.deepcopy(
        {
            "user_id": 1,
            "information": {},
            "locked_fields": {},
            "events": [  # dummy create event
                {"type": "create", "fqid": "not_used/1", "fields": {"f": 1}}
            ],
        }
    )


def test_locked_fqid(write_handler, connection_handler, valid_metadata):
    locked_fqid = MagicMock()
    connection_handler.fqid = MagicMock(return_value=locked_fqid)
    valid_metadata["locked_fields"]["a/1"] = 42

    with pytest.raises(ModelLocked) as e:
        write_handler.write(valid_metadata)

    assert e.value.key == locked_fqid


def test_locked_fqfield(write_handler, connection_handler, valid_metadata):
    locked_fqfield = MagicMock()
    connection_handler.to_json = json = MagicMock(side_effect=lambda data: data)
    connection_handler.fqfield = MagicMock(return_value=locked_fqfield)
    valid_metadata["locked_fields"]["a/1/f"] = 42

    with pytest.raises(ModelLocked) as e:
        write_handler.write(valid_metadata)

    assert e.value.key == locked_fqfield
    json.assert_called_with("f")


def test_locked_collectionfield(write_handler, connection_handler, valid_metadata):
    locked_collectionfield = MagicMock()
    connection_handler.collectionfield = MagicMock(return_value=locked_collectionfield)
    valid_metadata["locked_fields"]["a/f"] = 42

    with pytest.raises(ModelLocked) as e:
        write_handler.write(valid_metadata)

    assert e.value.key == locked_collectionfield
