import concurrent.futures
import os
from threading import Thread
from unittest.mock import MagicMock, patch

import psycopg2
import pytest
from psycopg2.extras import Json

from datastore.shared.di import injector
from datastore.shared.di.dependency_provider import service
from datastore.shared.postgresql_backend import (
    ConnectionHandler,
    setup_di as postgres_setup_di,
)
from datastore.shared.postgresql_backend.connection_handler import DatabaseError
from datastore.shared.postgresql_backend.pg_connection_handler import (
    ConnectionContext,
    PgConnectionHandlerService,
    retry_on_db_failure,
)
from datastore.shared.services import EnvironmentService, setup_di as util_setup_di
from datastore.shared.util import BadCodingError
from tests import reset_di  # noqa


@pytest.fixture(autouse=True)
def provide_di(reset_di):  # noqa
    util_setup_di()
    postgres_setup_di()
    yield


@pytest.fixture()
def handler(provide_di):
    yield injector.get(ConnectionHandler)


# Basic connection and connection context


def test_connection_context(handler):
    connection = MagicMock()
    handler.get_connection = gc = MagicMock(return_value=connection)
    handler.put_connection = pc = MagicMock()

    context = ConnectionContext(handler)
    assert context.connection_handler == handler
    gc.assert_not_called()

    with context:
        connection.__enter__.assert_called()
        connection.__exit__.assert_not_called()
        gc.assert_called()
    connection.__exit__.assert_called()
    pc.assert_called_with(connection, False)


def test_init_error():
    os.environ["DATASTORE_MIN_CONNECTIONS"] = "1"
    injector.get(EnvironmentService).cache = {}
    connect = MagicMock()
    connect.side_effect = psycopg2.Error
    with patch("psycopg2.connect", new=connect):
        with pytest.raises(DatabaseError):
            PgConnectionHandlerService()


def test_get_connection(handler):
    connection = MagicMock()
    handler._semaphore = semaphore = MagicMock()
    handler.connection_pool = pool = MagicMock()

    pool.getconn = gc = MagicMock(return_value=connection)

    assert handler.get_connection() == connection
    semaphore.acquire.assert_called()
    gc.assert_called()
    assert connection.autocommit is False
    assert handler.get_current_connection() == connection


def test_get_connection_twice_error(handler):
    handler.get_connection()
    with pytest.raises(BadCodingError):
        handler.get_connection()


def test_get_connection_ignore_invalid_connection(handler):
    old_conn = handler.get_connection()
    old_conn.close()
    new_conn = handler.get_connection()
    assert old_conn != new_conn


def test_get_connection_lock(handler):
    conn = handler.get_connection()
    thread = Thread(target=handler.get_connection)
    thread.start()
    thread.join(0.05)
    assert thread.is_alive()
    handler.put_connection(conn, False)
    thread.join(0.05)
    assert not thread.is_alive()


def test_get_connection_different():
    os.environ["DATASTORE_MAX_CONNECTIONS"] = "2"
    injector.get(EnvironmentService).cache = {}
    handler = service(PgConnectionHandlerService)()

    def get_connection_from_thread():
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(handler.get_connection)
            return future.result()

    connection1 = get_connection_from_thread()
    connection2 = get_connection_from_thread()
    assert connection1 != connection2


def test_put_connection(handler):
    connection = MagicMock()
    handler.get_current_connection = gcc = MagicMock(return_value=connection)
    handler.set_current_connection = scc = MagicMock()
    handler._semaphore = semaphore = MagicMock()
    handler.connection_pool = pool = MagicMock()

    pool.putconn = pc = MagicMock()

    handler.put_connection(connection, False)
    pc.assert_called_with(connection, close=False)
    semaphore.release.assert_called()
    gcc.assert_called()
    scc.assert_called_with(None)


def test_put_connection_invalid_connection(handler):
    handler._storage = MagicMock()
    handler._storage.connection = MagicMock()

    with pytest.raises(BadCodingError):
        handler.put_connection(MagicMock(), False)


@pytest.mark.skipif(
    not os.getenv("RUN_MANUAL_TESTS"), reason="needs manual intervention"
)
def test_postgres_connection_reset(handler):
    """
    Unfortunately, a manual restart of the postgres container is necessary to provoke
    the needed OperationalError. Run this test to see how the connection handler
    handles a short connection loss to the db.
    """
    try:
        with handler.get_connection_context():
            breakpoint()  # restart postgres here
            handler.execute("SELECT 1", [])
    except Exception:
        pass

    # this should still work without error
    with handler.get_connection_context():
        handler.execute("SELECT 1", [])


def test_get_connection_context(handler):
    with patch(
        "datastore.shared.postgresql_backend.pg_connection_handler.ConnectionContext"
    ) as context:
        handler.get_connection_context()
        context.assert_called_with(handler)


# Connection context and error handling


def test_connection_error_in_context(handler):
    connection = MagicMock()
    connection.closed = 1
    handler._semaphore = semaphore = MagicMock()
    handler.connection_pool = pool = MagicMock()
    pool.getconn = gc = MagicMock(return_value=connection)
    pool.putconn = pc = MagicMock()

    context = ConnectionContext(handler)
    with pytest.raises(DatabaseError):
        with context:
            gc.assert_called()
            raise psycopg2.Error("Test")

    # not blocked
    semaphore.acquire.assert_called_once()
    semaphore.release.assert_called_once()
    assert handler.get_current_connection() is None
    pc.assert_called_with(connection, close=True)


# Query methods


def test_to_json(handler):
    json = handler.to_json({"a": "a", "b": "b"})
    assert type(json) is Json
    assert str(json) == '\'{"a": "a", "b": "b"}\''


def setup_mocked_connection(handler):
    cursor = MagicMock(name="cursor")
    cursor.execute = MagicMock(name="execute")
    cursor_context = MagicMock(name="cursor_context")
    cursor_context.__enter__ = MagicMock(return_value=cursor, name="enter")
    mock = MagicMock(name="connection_mock")
    mock.cursor = MagicMock(return_value=cursor_context, name="cursor_func")
    handler.get_current_connection = MagicMock(return_value=mock)
    return cursor


def test_execute(handler):
    cursor = setup_mocked_connection(handler)

    handler.execute("", "")
    cursor.execute.assert_called()


def test_query(handler):
    cursor = setup_mocked_connection(handler)
    result = MagicMock()
    cursor.fetchall = MagicMock(return_value=result)

    assert handler.query("", "") == result
    cursor.execute.assert_called()
    cursor.fetchall.assert_called()


def test_query_single_value(handler):
    cursor = setup_mocked_connection(handler)
    result = MagicMock()
    result[0] = MagicMock()
    cursor.fetchone = MagicMock(return_value=result)

    assert handler.query_single_value("", "") == result[0]
    cursor.execute.assert_called()
    cursor.fetchone.assert_called()


def test_query_single_value_none(handler):
    cursor = setup_mocked_connection(handler)
    cursor.fetchone = MagicMock(return_value=None)

    assert handler.query_single_value("", "") is None


def test_query_list_of_single_values(handler):
    handler.query = MagicMock()
    handler.query_list_of_single_values("", "")
    handler.query.assert_called_with("", "", [], False)


def test_shutdown(handler):
    handler.connection_pool = pool = MagicMock()

    handler.shutdown()
    pool.closeall.assert_called()


# test retry_on_db_failure


def test_retry_on_db_failure():
    @retry_on_db_failure
    def test(counter):
        counter()
        error = psycopg2.OperationalError()
        raise DatabaseError("", error)

    counter = MagicMock()
    with pytest.raises(DatabaseError):
        test(counter)
    assert counter.call_count == 3


def test_retry_on_db_failure_raise_on_other_error():
    @retry_on_db_failure
    def test(counter):
        counter()
        error = psycopg2.Error()
        raise DatabaseError("", error)

    counter = MagicMock()
    with pytest.raises(DatabaseError):
        test(counter)
    assert counter.call_count == 1


def test_retry_on_db_failure_with_timeout():
    @retry_on_db_failure
    def test(counter):
        counter()
        error = psycopg2.OperationalError()
        raise DatabaseError("", error)

    counter = MagicMock()
    with patch(
        "datastore.shared.postgresql_backend.pg_connection_handler.sleep"
    ) as sleep:
        with pytest.raises(DatabaseError):
            test(counter)
    assert counter.call_count == 3
    assert sleep.call_count == 2
