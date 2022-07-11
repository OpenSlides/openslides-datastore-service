from unittest.mock import MagicMock

import pytest

from datastore.shared.di import injector
from datastore.shared.postgresql_backend import ConnectionHandler, SqlQueryHelper
from datastore.shared.postgresql_backend.sql_read_database_backend_service import (
    SqlReadDatabaseBackendService,
)
from datastore.shared.services import ReadDatabase
from datastore.shared.util import KEYSEPARATOR, ModelLocked
from datastore.writer.core import OccLocker
from datastore.writer.postgresql_backend import SqlOccLockerBackendService
from tests import reset_di  # noqa


@pytest.fixture(autouse=True)
def provide_di(reset_di):  # noqa
    injector.register_as_singleton(ConnectionHandler, MagicMock)
    injector.register(SqlQueryHelper, SqlQueryHelper)
    injector.register(ReadDatabase, SqlReadDatabaseBackendService)
    injector.register(OccLocker, SqlOccLockerBackendService)
    yield


@pytest.fixture()
def occ_locker(provide_di):
    yield injector.get(OccLocker)


@pytest.fixture()
def connection(provide_di):
    yield injector.get(ConnectionHandler)


@pytest.fixture()
def mock_write_request(provide_di):
    write_request = MagicMock()
    write_request.locked_fqids = None
    write_request.locked_fqfields = None
    write_request.locked_collectionfields = None
    yield write_request


def test_no_data(occ_locker, mock_write_request):
    occ_locker.assert_locked_fields(mock_write_request)
    assert occ_locker.get_locked_fqids({}) == []
    assert occ_locker.get_locked_fqfields({}) == []
    assert occ_locker.get_locked_collectionfields({}) == []


def test_raise_model_locked_fqid(occ_locker, connection, mock_write_request):
    connection.query_list_of_single_values = MagicMock(
        return_value=["test matched fqid"]
    )
    mock_write_request.locked_fqids = {"a/1": 2}
    with pytest.raises(ModelLocked) as e:
        occ_locker.assert_locked_fields(mock_write_request)
    assert e.value.keys == ["test matched fqid"]


def test_raise_model_locked_fqfield(occ_locker, connection, mock_write_request):
    connection.query_list_of_single_values = MagicMock(
        return_value=["test matched fqfield"]
    )
    mock_write_request.locked_fqfields = {"a/1/f": 2}
    with pytest.raises(ModelLocked) as e:
        occ_locker.assert_locked_fields(mock_write_request)
    assert e.value.keys == ["test matched fqfield"]


def test_raise_model_locked_collectionfield(occ_locker, connection, mock_write_request):
    connection.query_list_of_single_values = MagicMock(
        return_value=["test matched collectionfield"]
    )
    mock_write_request.locked_collectionfields = {"a/f": 2}
    with pytest.raises(ModelLocked) as e:
        occ_locker.assert_locked_fields(mock_write_request)
    assert e.value.keys == ["test matched collectionfield"]


def test_raise_model_locked_multiple_reduced_to_one(
    occ_locker, connection, mock_write_request
):
    connection.query_list_of_single_values = MagicMock(
        return_value=["test matched something"]
    )
    mock_write_request.locked_fqids = {"a/1": 2}
    mock_write_request.locked_fqfields = {"a/1/f": 2}
    with pytest.raises(ModelLocked) as e:
        occ_locker.assert_locked_fields(mock_write_request)
    assert e.value.keys == ["test matched something"]


def test_raise_model_locked_multiple_different(
    occ_locker, connection, mock_write_request
):
    connection.query_list_of_single_values = lambda query, args: [args[0]]
    mock_write_request.locked_fqids = {"a/1": 2}
    mock_write_request.locked_fqfields = {"a/1/f": 2}
    mock_write_request.locked_collectionfields = {"a/f": 2}
    with pytest.raises(ModelLocked) as e:
        occ_locker.assert_locked_fields(mock_write_request)
    assert set(e.value.keys) == {"a/f", "a/1"}


def test_query_arguments_fqid(occ_locker, connection):
    connection.query_list_of_single_values = qsv = MagicMock(return_value=None)

    occ_locker.get_locked_fqids({"a/1": 2, "b/3": 42})

    query = qsv.call_args.args[0]
    assert query.count("(fqid=%s and position>%s)") == 2
    args = qsv.call_args.args[1]
    assert (args == ["a/1", 2, "b/3", 42]) or (
        args == ["b/3", 42, "a/1", 2]
    )  # order of arguments is not determinated


def test_query_arguments_fqfield(occ_locker, connection):
    connection.query_list_of_single_values = qsv = MagicMock(return_value=None)

    occ_locker.get_locked_fqfields({"a/1/f": 2, "b/3/e": 42})

    query = qsv.call_args.args[0]
    assert query.count("(e.fqid=%s and e.position>%s)") == 2
    assert query.count("(fqid=%s and collectionfield = ANY(%s))") == 2
    args = qsv.call_args.args[1]
    assert (
        args
        == [
            "a/1",
            2,
            "b/3",
            42,
            KEYSEPARATOR,
            KEYSEPARATOR,
            "a/1",
            ["a/f"],
            "b/3",
            ["b/e"],
        ]
    ) or (
        args
        == [
            "b/3",
            42,
            "a/1",
            2,
            KEYSEPARATOR,
            KEYSEPARATOR,
            "b/3",
            ["b/e"],
            "a/1",
            ["a/f"],
        ]
    )  # order of arguments is not determinated


def test_query_arguments_collectionfield(occ_locker, connection):
    connection.query_list_of_single_values = qsv = MagicMock(return_value=None)

    occ_locker.get_locked_collectionfields({"a/f": 2, "b/e": 42})

    query = qsv.call_args.args[0]
    assert query.count("(cf.collectionfield=%s and e.position>%s)") == 2
    args = qsv.call_args.args[1]
    assert (args == ["a/f", 2, "b/e", 42]) or (
        args == ["b/e", 42, "a/f", 2]
    )  # order of arguments is not determinated
