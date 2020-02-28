import copy
from unittest.mock import MagicMock

import pytest

from tests.reset_di import reset_di  # noqa
from writer.core import (
    Database,
    Messaging,
    ModelDoesNotExist,
    ModelExists,
    OccLocker,
    ReadDatabase,
    setup_di as core_setup_di,
)
from writer.di import injector
from writer.flask_frontend.json_handlers import WriteHandler
from writer.postgresql_backend import SqlDatabaseBackendService
from writer.postgresql_backend.connection_handler import ConnectionHandler


class FakeConnectionHandler:
    def get_connection_context(self):
        return MagicMock()

    def execute(self, statement, arguments):
        if statement.startswith("insert into positions ("):
            self.create_position(statement, arguments)
        if statement.startswith("insert into models_lookup ("):
            self.create_model_lookup(statement, arguments)

    def create_position(self, statement, arguments):
        ""

    def create_model_lookup(self, statement, arguments):
        ""

    def query_single_value(self, query, arguments):
        if query == "select max(position) from positions":
            return self.get_max_position()
        if query.startswith("select exists(select 1"):
            return self.exists()
        if query.startswith("insert into events ("):
            return self.create_event(query, arguments)

    def get_max_position(self):
        ""

    def exists(self):
        ""

    def create_event(self, query, arguments):
        ""

    def query_list_of_single_values(self, query, arguments):
        if query.startswith("insert into collectionfields (collectionfield, position)"):
            return self.attach_fields()

    def attach_fields(self):
        ""

    def to_json(self, data):
        return data


@pytest.fixture(autouse=True)
def setup_di(reset_di):  # noqa
    injector.register_as_singleton(ConnectionHandler, FakeConnectionHandler)
    injector.register_as_singleton(ReadDatabase, MagicMock)
    injector.register(Database, SqlDatabaseBackendService)
    injector.register_as_singleton(OccLocker, lambda: MagicMock(unsafe=True))
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
        {"user_id": 1, "information": {}, "locked_fields": {}, "events": []}
    )


def test_insert_create_event(write_handler, connection_handler, valid_metadata):
    valid_metadata["events"].append(
        {"type": "create", "fqid": "a/1", "fields": {}}  # this is allowed
    )
    connection_handler.create_position = cp = MagicMock()
    position = MagicMock()
    connection_handler.get_max_position = MagicMock(return_value=position)
    connection_handler.exists = MagicMock(return_value=None)
    connection_handler.create_model_lookup = cml = MagicMock()
    connection_handler.create_event = ce = MagicMock()
    connection_handler.attach_fields = af = MagicMock(return_value=[])

    write_handler.write(valid_metadata)

    cp.assert_called_once()
    ce.assert_called_once()
    af.assert_called_once()
    # check if position is in the arguments
    assert position in ce.call_args.args[1]

    cml.assert_called_once()
    # check if fqid is in the arguments
    assert "a/1" in cml.call_args.args[1]


def test_insert_create_event_already_exists(
    write_handler, connection_handler, valid_metadata
):
    valid_metadata["events"].append(
        {"type": "create", "fqid": "a/1", "fields": {}}  # this is allowed
    )
    connection_handler.create_position = cp = MagicMock()
    connection_handler.get_max_position = MagicMock()
    connection_handler.exists = MagicMock(return_value=True)
    connection_handler.create_event = ce = MagicMock()

    with pytest.raises(ModelExists) as e:
        write_handler.write(valid_metadata)

    cp.assert_called_once()
    assert "a/1" == e.value.fqid
    assert ce.call_count == 0


def test_combined_update_delete_fields_events(
    write_handler, connection_handler, valid_metadata
):
    valid_metadata["events"].append(
        {"type": "update", "fqid": "a/1", "fields": {"f": 1, "none": None}}
    )
    connection_handler.create_position = cp = MagicMock()
    position = MagicMock()
    connection_handler.get_max_position = MagicMock(return_value=position)
    connection_handler.exists = exists = MagicMock(return_value=True)
    connection_handler.create_event = ce = MagicMock()
    connection_handler.attach_fields = af = MagicMock(return_value=[])

    write_handler.write(valid_metadata)

    cp.assert_called_once()
    assert exists.call_count == 2
    assert ce.call_count == 2
    assert af.call_count == 2
    # check if position is in the arguments
    assert position in ce.call_args_list[0].args[1]
    assert position in ce.call_args_list[1].args[1]


def test_combined_update_delete_fields_events_model_not_existent(
    write_handler, connection_handler, valid_metadata
):
    valid_metadata["events"].append(
        {"type": "update", "fqid": "a/1", "fields": {"f": 1, "none": None}}
    )
    connection_handler.create_position = cp = MagicMock()
    connection_handler.get_max_position = MagicMock()
    connection_handler.exists = MagicMock(return_value=None)
    connection_handler.create_event = ce = MagicMock()

    with pytest.raises(ModelDoesNotExist) as e:
        write_handler.write(valid_metadata)

    cp.assert_called_once()
    assert "a/1" == e.value.fqid
    assert ce.call_count == 0
