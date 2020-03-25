from unittest.mock import MagicMock

import pytest

from shared.core import ReadDatabase
from shared.di import injector
from shared.postgresql_backend import EVENT_TYPES, ConnectionHandler
from shared.postgresql_backend.sql_read_database_backend_service import (
    SqlReadDatabaseBackendService,
)
from shared.util import reset_di  # noqa


@pytest.fixture(autouse=True)
def provide_di(reset_di):  # noqa
    injector.register_as_singleton(ConnectionHandler, MagicMock)
    injector.register(ReadDatabase, SqlReadDatabaseBackendService)
    yield


@pytest.fixture()
def read_database(provide_di):
    yield injector.get(ReadDatabase)


@pytest.fixture()
def connection(provide_di):
    yield injector.get(ConnectionHandler)


def test_get_models(read_database, connection):
    fqid1 = MagicMock()
    model1 = MagicMock()
    fqid2 = MagicMock()
    model2 = MagicMock()
    connection.query = q = MagicMock(return_value=[(fqid1, model1), (fqid2, model2)])

    q_fqid1 = MagicMock()
    q_fqid2 = MagicMock()
    models = read_database.get_models([q_fqid1, q_fqid2])

    assert q.call_args.args[1] == [(q_fqid1, q_fqid2,)]
    assert models == {fqid1: model1, fqid2: model2}


def test_get_models_no_fqids(read_database):
    connection.query = q = MagicMock()

    assert read_database.get_models([]) == {}

    assert q.call_count == 0


def test_create_or_update_models(read_database, connection):
    fqid1 = MagicMock()
    model1 = MagicMock()
    fqid2 = MagicMock()
    model2 = MagicMock()
    models = {fqid1: model1, fqid2: model2}
    connection.execute = e = MagicMock()
    read_database.json = lambda x: x

    read_database.create_or_update_models(models)

    args = e.call_args.args[1]
    assert (args == [fqid1, model1, fqid2, model2]) or (
        args == [fqid2, model2, fqid1, model1]
    )


def test_create_or_update_models_no_models(read_database, connection):
    connection.execute = e = MagicMock()
    read_database.create_or_update_models([])
    e.assert_not_called()


def test_delete_models(read_database, connection):
    fqids = (
        MagicMock(),
        MagicMock(),
    )
    connection.execute = e = MagicMock()

    read_database.delete_models(fqids)

    assert e.call_args.args[1] == [fqids]


def test_delete_models_no_models(read_database, connection):
    connection.execute = e = MagicMock()
    read_database.delete_models([])
    e.assert_not_called()


def test_build_model_ignore_deleted(read_database, connection):
    fqid = MagicMock()
    events = MagicMock()
    model = MagicMock()
    connection.query = q = MagicMock(return_value=events)
    read_database.build_model_from_events = bmfe = MagicMock(return_value=model)

    result = read_database.build_model_ignore_deleted(fqid)

    assert q.call_args.args[1] == [fqid]
    bmfe.assert_called_with(events)
    assert result == model


def test_build_model_from_events_no_events(read_database):
    with pytest.raises(RuntimeError):
        read_database.build_model_from_events(None)
    with pytest.raises(RuntimeError):
        read_database.build_model_from_events([])


def test_build_model_from_events_no_first_create_event(read_database):
    with pytest.raises(AssertionError):
        read_database.build_model_from_events([(MagicMock(), MagicMock())])


def test_build_model_from_events_unknwon_event(read_database):
    with pytest.raises(RuntimeError):
        read_database.build_model_from_events(
            [(EVENT_TYPES.CREATE, MagicMock()), (MagicMock(), MagicMock())]
        )


def test_build_model_from_events_update_event(read_database):
    base_model = MagicMock()
    base_model.update = u = MagicMock()
    update_event = MagicMock()

    result = read_database.build_model_from_events(
        [(EVENT_TYPES.CREATE, base_model), (EVENT_TYPES.UPDATE, update_event)]
    )

    u.assert_called_with(update_event)
    assert result == base_model


def test_build_model_from_events_delete_fields_event(read_database):
    field = MagicMock()
    base_model = {field: MagicMock}
    delete_fields_event = [field]

    result = read_database.build_model_from_events(
        [
            (EVENT_TYPES.CREATE, base_model),
            (EVENT_TYPES.DELETE_FIELDS, delete_fields_event),
        ]
    )

    assert result == {}


def test_json(read_database, connection):
    value = MagicMock()
    connection.to_json = tj = MagicMock(return_value=value)
    data = MagicMock()

    assert read_database.json(data) == value
    tj.assert_called_with(data)
