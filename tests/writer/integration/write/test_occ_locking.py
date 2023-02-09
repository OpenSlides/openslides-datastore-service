import copy
from dataclasses import asdict
from unittest.mock import MagicMock

import pytest

from datastore.shared.di import injector
from datastore.shared.postgresql_backend import ConnectionHandler, SqlQueryHelper
from datastore.shared.services import EnvironmentService, ReadDatabase
from datastore.shared.util import FilterOperator, ModelLocked
from datastore.writer.core import (
    Database,
    Messaging,
    OccLocker,
    setup_di as core_setup_di,
)
from datastore.writer.flask_frontend.json_handlers import WriteHandler
from datastore.writer.postgresql_backend import SqlOccLockerBackendService
from tests import reset_di  # noqa


class FakeConnectionHandler:
    def query_list_of_single_values(self, query, arguments):
        if query.startswith("with all_together as"):
            return [self.fqfield()]
        elif query.startswith("select fqid from events"):
            return [self.fqid()]
        elif query.startswith("select collectionfield from collectionfields"):
            return [self.collectionfield()]

    def fqid(self):
        """"""

    def fqfield(self):
        """"""

    def collectionfield(self):
        """"""


@pytest.fixture(autouse=True)
def setup_di(reset_di):  # noqa
    injector.register_as_singleton(ConnectionHandler, FakeConnectionHandler)
    injector.register(SqlQueryHelper, SqlQueryHelper)
    injector.register(OccLocker, SqlOccLockerBackendService)
    injector.register_as_singleton(Database, MagicMock)
    injector.register_as_singleton(ReadDatabase, MagicMock)
    injector.register_as_singleton(Messaging, MagicMock)
    injector.register(EnvironmentService, EnvironmentService)
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

    assert e.value.keys == [locked_fqid]


def test_locked_fqfield(write_handler, connection_handler, valid_metadata):
    locked_fqfield = MagicMock()
    connection_handler.fqfield = MagicMock(return_value=locked_fqfield)
    valid_metadata["locked_fields"]["a/1/f"] = 42

    with pytest.raises(ModelLocked) as e:
        write_handler.write(valid_metadata)

    assert e.value.keys == [locked_fqfield]


def test_locked_collectionfield(write_handler, connection_handler, valid_metadata):
    locked_collectionfield = MagicMock()
    connection_handler.collectionfield = MagicMock(return_value=locked_collectionfield)
    valid_metadata["locked_fields"]["a/f"] = 42

    with pytest.raises(ModelLocked) as e:
        write_handler.write(valid_metadata)

    assert e.value.keys == [locked_collectionfield]


def test_locked_collectionfield_with_filter(
    write_handler, connection_handler, valid_metadata
):
    locked_collectionfield = MagicMock()
    connection_handler.collectionfield = MagicMock(return_value=locked_collectionfield)
    valid_metadata["locked_fields"]["a/f"] = {
        "position": 42,
        "filter": asdict(FilterOperator("field", "=", "value")),
    }

    with pytest.raises(ModelLocked) as e:
        write_handler.write(valid_metadata)

    assert e.value.keys == [locked_collectionfield]


def test_locked_collectionfield_with_filter_without_filter(
    write_handler, connection_handler, valid_metadata
):
    locked_collectionfield = MagicMock()
    connection_handler.collectionfield = MagicMock(return_value=locked_collectionfield)
    valid_metadata["locked_fields"]["a/f"] = {"position": 42}

    with pytest.raises(ModelLocked) as e:
        write_handler.write(valid_metadata)

    assert e.value.keys == [locked_collectionfield]
