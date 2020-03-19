from unittest.mock import MagicMock

import pytest

from shared.core import ModelLocked
from shared.di import injector
from shared.postgresql_backend import ConnectionHandler
from shared.tests import reset_di  # noqa
from writer.core import OccLocker
from writer.postgresql_backend import SqlOccLockerBackendService


@pytest.fixture(autouse=True)
def provide_di(reset_di):  # noqa
    injector.register_as_singleton(ConnectionHandler, MagicMock)
    injector.register(OccLocker, SqlOccLockerBackendService)
    yield


@pytest.fixture()
def occ_locker(provide_di):
    yield injector.get(OccLocker)


@pytest.fixture()
def connection(provide_di):
    yield injector.get(ConnectionHandler)


def test_no_data(occ_locker):
    occ_locker.assert_fqid_positions({})
    occ_locker.assert_fqfield_positions({})
    occ_locker.assert_collectionfield_positions({})


def test_raise_model_locked_fqid(occ_locker, connection):
    connection.query_single_value = MagicMock(return_value="test matched fqid")
    with pytest.raises(ModelLocked) as e:
        occ_locker.assert_fqid_positions({"a/1": 2})
    assert e.value.key == "test matched fqid"


def test_raise_model_locked_fqfield(occ_locker, connection):
    connection.query_single_value = MagicMock(return_value="test matched fqfield")
    with pytest.raises(ModelLocked) as e:
        occ_locker.assert_fqfield_positions({"a/1/f": 2})
    assert e.value.key == "test matched fqfield"


def test_raise_model_locked_collectionfield(occ_locker, connection):
    connection.query_single_value = MagicMock(
        return_value="test matched collectionfield"
    )
    with pytest.raises(ModelLocked) as e:
        occ_locker.assert_collectionfield_positions({"a/f": 2})
    assert e.value.key == "test matched collectionfield"


def test_query_arguments_fqid(occ_locker, connection):
    connection.query_single_value = qsv = MagicMock(return_value=None)

    occ_locker.assert_fqid_positions({"a/1": 2, "b/3": 42})

    query = qsv.call_args.args[0]
    assert query.count("(fqid=%s and position>%s)") == 2
    args = qsv.call_args.args[1]
    assert (args == ["a/1", 2, "b/3", 42]) or (
        args == ["b/3", 42, "a/1", 2]
    )  # order of arguments is not determinated


def test_query_arguments_fqfield(occ_locker, connection):
    connection.query_single_value = qsv = MagicMock(return_value=None)

    occ_locker.assert_fqfield_positions({"a/1/f": 2, "b/3/e": 42})

    query = qsv.call_args.args[0]
    assert query.count("(fqid=%s and position>%s)") == 2
    assert query.count("(e.fqid=%s and cf.collectionfield=%s)") == 2
    args = qsv.call_args.args[1]
    assert (args == ["a/1", 2, "b/3", 42, "a/1", "a/f", "b/3", "b/e"]) or (
        args == ["b/3", 42, "a/1", 2, "b/3", "b/e", "a/1", "a/f"]
    )  # order of arguments is not determinated


def test_query_arguments_collectionfield(occ_locker, connection):
    connection.query_single_value = qsv = MagicMock(return_value=None)

    occ_locker.assert_collectionfield_positions({"a/f": 2, "b/e": 42})

    query = qsv.call_args.args[0]
    assert query.count("(collectionfield=%s and position>%s)") == 2
    args = qsv.call_args.args[1]
    assert (args == ["a/f", 2, "b/e", 42]) or (
        args == ["b/e", 42, "a/f", 2]
    )  # order of arguments is not determinated
