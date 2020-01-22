from unittest.mock import MagicMock

import pytest

from tests.reset_di import reset_di  # noqa
from writer.core import (
    DbCreateEvent,
    DbDeleteEvent,
    DbDeleteFieldsEvent,
    DbRestoreEvent,
    DbUpdateEvent,
    InvalidFormat,
    ModelDoesNotExist,
    ModelExists,
    ModelNotDeleted,
)
from writer.core.database import Database
from writer.di import injector
from writer.postgresql_backend import SqlDatabaseBackendService
from writer.postgresql_backend.connection_handler import ConnectionHandler
from writer.postgresql_backend.sql_database_backend_service import (
    COLLECTION_MAX_LEN,
    COLLECTIONFIELD_MAX_LEN,
    EVENT_TYPES,
    FQID_MAX_LEN,
)


@pytest.fixture(autouse=True)
def provide_di(reset_di):  # noqa
    injector.register_as_singleton(ConnectionHandler, MagicMock)
    injector.register(Database, SqlDatabaseBackendService)
    yield


@pytest.fixture()
def sql_backend(provide_di):
    yield injector.get(Database)


@pytest.fixture()
def connection(provide_di):
    yield injector.get(ConnectionHandler)


def test_sql_backend_creation(sql_backend):
    assert bool(sql_backend)


def test_get_context(sql_backend, connection):
    connection.get_connection_context = MagicMock(return_value="my_return_value")

    assert sql_backend.get_context() == "my_return_value"


def test_json(sql_backend, connection):
    connection.to_json = tj = MagicMock(return_value="my_return_value")

    assert sql_backend.json("my_data") == "my_return_value"
    tj.assert_called_with("my_data")


class TestExistsQuery:
    def test_exists_query_did_not_found_someting(self, sql_backend, connection):
        connection.query_single_value = MagicMock(return_value=False)

        assert sql_backend.exists_query("", "", None) is False

    def test_exists_query_found_something(self, sql_backend, connection):
        connection.query_single_value = MagicMock(return_value=True)

        assert sql_backend.exists_query("", "", None)

    def test_exists_query_passed_arguments(self, sql_backend, connection):
        connection.query_single_value = qsv = MagicMock(return_value=None)
        args = MagicMock()

        sql_backend.exists_query("", "", args)

        assert qsv.call_args.args[1] == args

    def test_exists_query_table_name_and_conditions(self, sql_backend, connection):
        connection.query_single_value = qsv = MagicMock(return_value=None)

        sql_backend.exists_query("my_table", "some_conditions", None)

        assert "my_table" in qsv.call_args.args[0]
        assert "some_conditions" in qsv.call_args.args[0]


class TestInsertEvents:
    def test_insert_no_events(self, sql_backend):
        sql_backend.create_position = cp = MagicMock()
        with pytest.raises(RuntimeError):
            sql_backend.insert_events([], {}, 1)
        cp.assert_not_called()

    def test_set_position(self, sql_backend):
        sql_backend.create_position = MagicMock(return_value=239)
        sql_backend.update_modified_collectionfields = MagicMock()
        sql_backend.insert_event = MagicMock()
        event = MagicMock()
        event.fqid = "a/1"

        position = sql_backend.insert_events([event], {}, 1)

        assert position == 239

    def test_call_insert_event(self, sql_backend):
        sql_backend.create_position = MagicMock()
        sql_backend.update_modified_collectionfields = MagicMock()
        sql_backend.insert_event = ie = MagicMock()
        event1 = MagicMock()
        event1.fqid = "a/1"
        event2 = MagicMock()
        event2.fqid = "a/2"

        sql_backend.insert_events([event1, event2], {}, 1)

        assert ie.call_count == 2
        assert ie.call_args_list[0].args[0] == event1
        assert ie.call_args_list[1].args[0] == event2

    def test_call_update_modified_collectionfields(self, sql_backend):
        sql_backend.create_position = MagicMock(return_value=239)
        sql_backend.update_modified_collectionfields = umcf = MagicMock()
        sql_backend.insert_event = MagicMock()
        event = MagicMock()
        event.fqid = "a/1"

        sql_backend.insert_events([event], {}, 1)

        umcf.assert_called_with([event], 239)


class TestUpdateCollectionFields:
    def test_update_modified_collectionfields(self, sql_backend):
        sql_backend.update_modified_collectionfields_in_database = umcfid = MagicMock()
        position = MagicMock()
        event = MagicMock()
        event.fqid = "a/1"
        event.get_modified_fields = MagicMock(return_value=["f1", "f2", "f1"])

        sql_backend.update_modified_collectionfields([event], position)

        umcfid.assert_called_with(set(("a/f1", "a/f2",)), position)

    def test_update_modified_collectionfields_in_db_too_long(self, sql_backend):
        cf = "x" * (COLLECTIONFIELD_MAX_LEN + 1)
        with pytest.raises(InvalidFormat) as e:
            sql_backend.update_modified_collectionfields_in_database([cf], None)
        assert cf in e.value.msg

    def test_update_modified_collectionfields_in_db(self, sql_backend, connection):
        connection.execute = ex = MagicMock()
        position = MagicMock()
        cf1 = "a/f1"
        cf2 = "b/f2"

        sql_backend.update_modified_collectionfields_in_database([cf1, cf2], position)

        query = ex.call_args.args[0]
        assert query.count("(%s, %s)") == 2
        args = ex.call_args.args[1]
        assert args == ["a/f1", position, "b/f2", position]

    def test_insert_fqid_too_long(self, sql_backend):
        sql_backend.create_position = MagicMock(return_value=239)
        event = MagicMock()
        event.fqid = "x" * FQID_MAX_LEN + "/1"

        with pytest.raises(InvalidFormat) as e:
            sql_backend.insert_events([event], {}, 1)
        assert event.fqid in e.value.msg


def test_create_position(sql_backend, connection):
    sql_backend.json = json = MagicMock(side_effect=lambda data: data)
    connection.query_single_value = MagicMock(return_value=2844)
    connection.execute = execute = MagicMock()

    position = sql_backend.create_position({"some": "data", "is": ["given"]}, 42)

    assert position == 2844
    execute.assert_called_once()
    json.assert_called_once()


class TestInsertEventDispatching:
    def test_create_event(self, sql_backend):
        sql_backend.insert_create_event = ie = MagicMock()
        event = DbCreateEvent("a/1", {"f": "Value"})
        position = MagicMock()

        sql_backend.insert_event(event, position)

        ie.assert_called_with(event, position)

    def test_update_event(self, sql_backend):
        sql_backend.insert_update_event = ie = MagicMock()
        event = DbUpdateEvent("a/1", {"f": "Value"})
        position = MagicMock()

        sql_backend.insert_event(event, position)

        ie.assert_called_with(event, position)

    def test_delete_fields_event(self, sql_backend):
        sql_backend.insert_delete_fields_event = ie = MagicMock()
        event = DbDeleteFieldsEvent("a/1", ["f"])
        position = MagicMock()

        sql_backend.insert_event(event, position)

        ie.assert_called_with(event, position)

    def test_delete_event(self, sql_backend):
        sql_backend.insert_delete_event = ie = MagicMock()
        event = DbDeleteEvent("a/1")
        position = MagicMock()

        sql_backend.insert_event(event, position)

        ie.assert_called_with(event, position)

    def test_restore_event(self, sql_backend):
        sql_backend.insert_restore_event = ie = MagicMock()
        event = DbRestoreEvent("a/1")
        position = MagicMock()

        sql_backend.insert_event(event, position)

        ie.assert_called_with(event, position)


class TestInsertCreateEvent:
    def test_raise_model_exists(self, sql_backend):
        sql_backend.exists_query = MagicMock(return_value=True)
        event = MagicMock()
        event.fqid = "a/1"

        with pytest.raises(ModelExists) as e:
            sql_backend.insert_create_event(event, None)

        assert event.fqid == e.value.fqid

    def test_insert(self, sql_backend, connection):
        sql_backend.exists_query = MagicMock(return_value=False)
        sql_backend.json = json = MagicMock(side_effect=lambda x: x)
        connection.execute = ex = MagicMock()
        event = MagicMock()
        event.fqid = "a/1"
        event.field_data = "test_data"
        event.get_fields = MagicMock(return_value="f")
        position = MagicMock()

        sql_backend.insert_create_event(event, position)

        assert ex.call_count == 2
        args = ex.call_args_list[0].args[1]
        assert args == [position, event.fqid, EVENT_TYPES.CREATE, "test_data", "f"]
        assert json.call_count == 2


def test_insert_update_event(sql_backend, connection):
    sql_backend.assert_exists = ae = MagicMock()
    sql_backend.json = json = MagicMock(side_effect=lambda x: x)
    connection.execute = ex = MagicMock()
    event = MagicMock()
    event.fqid = "a/1"
    event.field_data = "test_data"
    event.get_fields = MagicMock(return_value="f")
    position = MagicMock()

    sql_backend.insert_update_event(event, position)

    ae.assert_called_with(event.fqid)
    args = ex.call_args.args[1]
    assert args == [position, event.fqid, EVENT_TYPES.UPDATE, "test_data", "f"]
    assert json.call_count == 2


def test_insert_delete_fields_event(sql_backend, connection):
    sql_backend.assert_exists = ae = MagicMock()
    sql_backend.json = json = MagicMock(side_effect=lambda x: x)
    connection.execute = ex = MagicMock()
    event = MagicMock()
    event.fqid = "a/1"
    event.fields = ["f1", "f2"]
    position = MagicMock()

    sql_backend.insert_delete_fields_event(event, position)

    ae.assert_called_with(event.fqid)
    args = ex.call_args.args[1]
    assert args == [
        position,
        event.fqid,
        EVENT_TYPES.DELETE_FIELDS,
        event.fields,
        event.fields,
    ]
    assert json.call_count == 2


def test_insert_delete_event(sql_backend, connection):
    sql_backend.assert_exists = ae = MagicMock()
    sql_backend.get_current_fields_from_model = gcffm = MagicMock(
        return_value="some_fields"
    )
    sql_backend.json = json = MagicMock(side_effect=lambda x: x)
    connection.execute = ex = MagicMock()
    event = MagicMock()
    event.fqid = "a/1"
    event.set_modified_fields = MagicMock()
    event.get_fields = MagicMock(return_value="f")
    position = MagicMock()

    sql_backend.insert_delete_event(event, position)

    ae.assert_called_with(event.fqid)
    gcffm.assert_called_with(event.fqid)
    event.set_modified_fields.assert_called_with("some_fields")
    assert ex.call_count == 2
    args = ex.call_args_list[0].args[1]
    assert args == [position, event.fqid, EVENT_TYPES.DELETE, None, "some_fields"]
    assert json.call_count == 2


def test_assert_exists(sql_backend):
    sql_backend.exists_query = MagicMock(return_value=False)
    fqid = "a/1"

    with pytest.raises(ModelDoesNotExist) as e:
        sql_backend.assert_exists(fqid)
    assert e.value.fqid == fqid


def test_get_current_fields_from_model(sql_backend, connection):
    connection.query_list_of_single_values = qlosv = MagicMock(
        return_value="the_result"
    )
    fqid = "a/1"

    assert sql_backend.get_current_fields_from_model(fqid) == "the_result"
    args = qlosv.call_args.args[1]
    assert args == [fqid]


def test_insert_restore_event_raises_model_not_deleted(sql_backend, connection):
    sql_backend.exists_query = MagicMock(return_value=False)
    event = MagicMock()
    event.fqid = "a/1"

    with pytest.raises(ModelNotDeleted) as e:
        sql_backend.insert_restore_event(event, None)
    assert e.value.fqid == event.fqid


def test_insert_restore_event(sql_backend, connection):
    sql_backend.exists_query = eq = MagicMock(return_value=True)
    sql_backend.get_current_fields_from_deleted_model = gcffdm = MagicMock(
        return_value="some_fields"
    )
    sql_backend.json = json = MagicMock(side_effect=lambda x: x)
    connection.execute = ex = MagicMock()
    event = MagicMock()
    event.fqid = "a/1"
    event.set_modified_fields = MagicMock()
    event.get_fields = MagicMock(return_value="f")
    position = MagicMock()

    sql_backend.insert_restore_event(event, position)

    eq.assert_called_once()
    gcffdm.assert_called_with(event.fqid)
    event.set_modified_fields.assert_called_with("some_fields")
    assert ex.call_count == 2
    args = ex.call_args_list[0].args[1]
    assert args == [position, event.fqid, EVENT_TYPES.RESTORE, None, "some_fields"]
    assert json.call_count == 2


def test_get_current_fields_from_deleted_model(sql_backend, connection):
    connection.query_single_value = qsv = MagicMock(return_value="the_result")
    fqid = "a/1"

    assert sql_backend.get_current_fields_from_deleted_model(fqid) == "the_result"
    args = qsv.call_args.args[1]
    assert args == [fqid]


class TestReserveNextIds:
    def test_wrong_amount(self, sql_backend):
        with pytest.raises(InvalidFormat):
            sql_backend.reserve_next_ids("my_collection", 0)

    def test_empty_collection(self, sql_backend):
        with pytest.raises(InvalidFormat):
            sql_backend.reserve_next_ids("", 1)

    def test_collection_too_long(self, sql_backend):
        with pytest.raises(InvalidFormat):
            sql_backend.reserve_next_ids("x" * (COLLECTION_MAX_LEN + 1), 1)

    def test_initial_collection_query(self, sql_backend, connection):
        connection.query_single_value = MagicMock(return_value=None)
        connection.execute = ex = MagicMock()

        result = sql_backend.reserve_next_ids("my_collection", 3)

        assert result == [1, 2, 3]
        ex.assert_called_once()
        args = ex.call_args.args[1]
        assert args == ["my_collection", 4]

    def test_collection_query(self, sql_backend, connection):
        connection.query_single_value = MagicMock(return_value=4)
        connection.execute = ex = MagicMock()

        result = sql_backend.reserve_next_ids("my_collection", 3)

        assert result == [4, 5, 6]
        ex.assert_called_once()
        args = ex.call_args.args[1]
        assert args == ["my_collection", 7]
