from unittest.mock import MagicMock

import pytest

from datastore.shared.di import injector
from datastore.shared.postgresql_backend import EVENT_TYPES, ConnectionHandler
from datastore.shared.postgresql_backend.connection_handler import DatabaseError
from datastore.shared.postgresql_backend.sql_query_helper import SqlQueryHelper
from datastore.shared.postgresql_backend.sql_read_database_backend_service import (
    SqlReadDatabaseBackendService,
)
from datastore.shared.services.read_database import (
    CountFilterQueryFieldsParameters,
    ReadDatabase,
)
from datastore.shared.util import (
    META_DELETED,
    META_POSITION,
    BadCodingError,
    DeletedModelsBehaviour,
    FilterOperator,
    ModelDoesNotExist,
)
from tests import reset_di  # noqa


@pytest.fixture(autouse=True)
def provide_di(reset_di):  # noqa
    injector.register_as_singleton(ConnectionHandler, MagicMock)
    injector.register(SqlQueryHelper, SqlQueryHelper)
    injector.register(ReadDatabase, SqlReadDatabaseBackendService)
    yield


@pytest.fixture()
def read_database(provide_di):
    yield injector.get(ReadDatabase)


@pytest.fixture()
def connection(provide_di):
    yield injector.get(ConnectionHandler)


@pytest.fixture()
def query_helper(provide_di):
    yield injector.get(SqlQueryHelper)


def test_database_error():
    e = DatabaseError("msg")
    assert e.msg == "msg"


def test_get_connection(read_database: ReadDatabase):
    connection = MagicMock()
    connection.get_connection_context = MagicMock(return_value="test")
    read_database.connection = connection

    assert read_database.get_context() == "test"
    connection.get_connection_context.assert_called()


def test_get(read_database: ReadDatabase):
    fqid = "c/1"
    model = MagicMock()
    read_database.get_many = q = MagicMock(return_value={fqid: model})

    model = read_database.get(fqid, [])

    assert q.call_args.args[0] == [fqid]
    assert model == model


def test_get_invalid(read_database: ReadDatabase):
    fqid = "c/1"
    read_database.get_many = q = MagicMock(return_value={})

    with pytest.raises(ModelDoesNotExist):
        read_database.get(fqid, [])

    assert q.call_args.args[0] == [fqid]


def test_get_many(
    read_database: ReadDatabase,
    connection: ConnectionHandler,
    query_helper: SqlQueryHelper,
):
    fqid1 = "c/1"
    model1 = MagicMock()
    fqid2 = "c/2"
    model2 = MagicMock()
    connection.query = q = MagicMock(
        return_value=[{"fqid": fqid1, "data": model1}, {"fqid": fqid2, "data": model2}]
    )

    q_fqid1 = MagicMock()
    q_fqid2 = MagicMock()
    models = read_database.get_many([q_fqid1, q_fqid2])

    assert q.call_args.args[1] == [(q_fqid1, q_fqid2)]
    assert models == {fqid1: model1, fqid2: model2}


def test_get_many_no_fqids(read_database: ReadDatabase, connection: ConnectionHandler):
    connection.query = q = MagicMock()

    assert read_database.get_many([], {}) == {}

    assert q.call_count == 0


def test_get_all(read_database: ReadDatabase):
    res = MagicMock()
    read_database.fetch_models = f = MagicMock(return_value=res)

    models = read_database.get_all("c", ["f"])

    f.assert_called()
    assert models == res


def test_get_everything(read_database: ReadDatabase, connection: ConnectionHandler):
    res = [{"__fqid__": "a/2", "data": {}}, {"__fqid__": "a/1", "data": {}}]
    connection.query = f = MagicMock(return_value=res)

    models = read_database.get_everything(
        get_deleted_models=DeletedModelsBehaviour.ALL_MODELS
    )

    f.assert_called()
    assert models == {"a": {1: {"id": 1}, 2: {"id": 2}}}


def test_filter(read_database: ReadDatabase):
    res = MagicMock()
    read_database.fetch_models = f = MagicMock(return_value=res)
    filter = FilterOperator("a", "=", "a")

    models = read_database.filter("c", filter, [])

    f.assert_called()
    assert models == res


def test_aggregate(read_database: ReadDatabase, connection: ConnectionHandler):
    res = MagicMock()
    res.copy = lambda: res
    connection.query = q = MagicMock(return_value=[res])
    filter = FilterOperator("a", "=", "a")
    param = CountFilterQueryFieldsParameters()

    models = read_database.aggregate("c", filter, param)

    q.assert_called()
    assert models == res


def test_fetch_models(read_database: ReadDatabase, connection: ConnectionHandler):
    args = [MagicMock(), MagicMock(), MagicMock()]
    row = MagicMock()
    row["data"] = MagicMock()
    connection.query = q = MagicMock(return_value=[row])

    models = read_database.fetch_models(*args, [])

    q.assert_called_with(*args)
    assert list(models.values()) == [row["data"]]


def test_fetch_models_mapped_fields(
    read_database: ReadDatabase, connection: ConnectionHandler
):
    args = [MagicMock(), MagicMock(), MagicMock()]
    row = MagicMock()
    row.copy = lambda: row
    connection.query = q = MagicMock(return_value=[row])

    models = read_database.fetch_models(*args, [1])

    q.assert_called_with(*args)
    assert list(models.values()) == [row]


def test_build_models_from_result(
    read_database: ReadDatabase, query_helper: SqlQueryHelper
):
    row = {"fqid": "a/1", "field": "a"}
    mfpc = {"a/1": ["field"]}
    result = read_database.build_models_from_result([row], mfpc)
    assert result == {row["fqid"]: {"field": "a"}}


def test_build_model_ignore_deleted(
    read_database: ReadDatabase, connection: ConnectionHandler
):
    fqid = MagicMock()
    events = [{"fqid": fqid, "data": MagicMock()}, {"fqid": fqid, "data": MagicMock()}]
    model = MagicMock()
    connection.query = q = MagicMock(return_value=events)
    read_database.build_model_from_events = bmfe = MagicMock(return_value=model)

    result = read_database.build_model_ignore_deleted(fqid)

    assert q.call_args.args[1] == [(fqid,)]
    bmfe.assert_called_with(events)
    assert result == model


def test_build_model_ignore_deleted_invalid_fqid(
    read_database: ReadDatabase, connection: ConnectionHandler
):
    fqid = MagicMock()
    events = [{"fqid": MagicMock()}]
    model = MagicMock()
    connection.query = q = MagicMock(return_value=events)
    read_database.build_model_from_events = bmfe = MagicMock(return_value=model)

    with pytest.raises(ModelDoesNotExist):
        read_database.build_model_ignore_deleted(fqid)

    assert q.call_args.args[1] == [(fqid,)]
    bmfe.assert_called_with(events)


def test_build_model_ignore_deleted_position(
    read_database: ReadDatabase, connection: ConnectionHandler
):
    fqid = MagicMock()
    pos = 42
    events = [{"fqid": fqid, "data": MagicMock()}, {"fqid": fqid, "data": MagicMock()}]
    model = MagicMock()
    connection.query = q = MagicMock(return_value=events)
    read_database.build_model_from_events = bmfe = MagicMock(return_value=model)

    result = read_database.build_model_ignore_deleted(fqid, pos)

    assert "position <= %s" in q.call_args.args[0]
    assert q.call_args.args[1] == [(fqid,), pos]
    bmfe.assert_called_with(events)
    assert result == model


def test_build_model_from_events_no_events(read_database: ReadDatabase):
    with pytest.raises(BadCodingError):
        read_database.build_model_from_events(None)
    with pytest.raises(BadCodingError):
        read_database.build_model_from_events([])


def test_build_model_from_events_no_first_create_event(read_database: ReadDatabase):
    with pytest.raises(AssertionError):
        read_database.build_model_from_events(
            [{"type": MagicMock(), "data": MagicMock()}]
        )


def test_build_model_from_events_unknown_event(read_database: ReadDatabase):
    with pytest.raises(BadCodingError):
        read_database.build_model_from_events(
            [
                {"type": EVENT_TYPES.CREATE, "data": MagicMock()},
                {"type": MagicMock(), "data": MagicMock()},
            ]
        )


def test_build_model_from_events_delete_fields_event(read_database: ReadDatabase):
    field = MagicMock()
    base_model = {field: MagicMock}
    delete_fields_event = [field]

    result = read_database.build_model_from_events(
        [
            {"type": EVENT_TYPES.CREATE, "data": base_model},
            {
                "type": EVENT_TYPES.DELETE_FIELDS,
                "data": delete_fields_event,
                "position": 0,
            },
        ]
    )

    assert result == {META_DELETED: False, META_POSITION: 0}


def test_is_deleted(read_database: ReadDatabase):
    fqid = MagicMock()
    result = MagicMock()
    read_database.get_deleted_status = gds = MagicMock(return_value={fqid: result})

    assert read_database.is_deleted(fqid) == result
    assert gds.call_args.args[0] == [fqid]


def test_is_deleted_invalid_fqid(read_database: ReadDatabase):
    read_database.get_deleted_status = MagicMock(return_value={})

    with pytest.raises(ModelDoesNotExist):
        read_database.is_deleted(MagicMock())


def test_get_deleted_status(read_database: ReadDatabase, connection: ConnectionHandler):
    fqid = MagicMock()
    deleted = MagicMock()
    result = [{"fqid": fqid, "deleted": deleted}]
    connection.query = q = MagicMock(return_value=result)

    assert read_database.get_deleted_status([fqid]) == {fqid: deleted}
    assert "from models " in q.call_args.args[0]
    assert q.call_args.args[1] == [(fqid,)]


def test_get_deleted_status_position(
    read_database: ReadDatabase, connection: ConnectionHandler
):
    fqid = MagicMock()
    result = [{"fqid": fqid, "type": EVENT_TYPES.DELETE}]
    connection.query = q = MagicMock(return_value=result)

    assert read_database.get_deleted_status([fqid], 42) == {fqid: True}
    assert "from events" in q.call_args.args[0]
    assert q.call_args.args[1] == [(fqid,)]


def test_get_position(read_database: ReadDatabase, connection: ConnectionHandler):
    connection.query_single_value = q = MagicMock(return_value=42)
    assert read_database.get_max_position() == 42
    q.assert_called_with("select max(position) from positions", [])


def test_is_empty(read_database: ReadDatabase, connection: ConnectionHandler):
    connection.query_single_value = q = MagicMock(return_value=True)
    assert read_database.is_empty() is False
    q.assert_called_with("select exists(select * from positions)", [])


def test_json(read_database: ReadDatabase, connection: ConnectionHandler):
    value = MagicMock()
    connection.to_json = tj = MagicMock(return_value=value)
    data = MagicMock()

    assert read_database.json(data) == value
    tj.assert_called_with(data)


def test_get_current_migration_index_cached(
    read_database: ReadDatabase, connection: ConnectionHandler
):
    connection.query = query = MagicMock(return_value=[[None, None]])
    assert read_database.get_current_migration_index() == -1
    query.assert_called_once()

    # second try; now it should be cached (so still called only once)
    assert read_database.get_current_migration_index() == -1
    query.assert_called_once()
