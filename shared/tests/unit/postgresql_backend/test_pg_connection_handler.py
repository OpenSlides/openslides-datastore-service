from unittest.mock import MagicMock, patch

import psycopg2
import pytest
from psycopg2.extras import Json

from shared.di import injector
from shared.postgresql_backend import ConnectionHandler, setup_di as postgres_setup_di
from shared.postgresql_backend.connection_handler import DatabaseError
from shared.postgresql_backend.pg_connection_handler import ConnectionContext
from shared.tests import reset_di  # noqa
from shared.util import BadCodingError, setup_di as util_setup_di


@pytest.fixture(autouse=True)
def provide_di(reset_di):  # noqa
    util_setup_di()
    postgres_setup_di()
    yield


@pytest.fixture()
def connection(provide_di):
    yield injector.get(ConnectionHandler)


def test_connection_context(connection):
    connection.connection = mock = MagicMock()
    connection.set_transaction_running = set_tr = MagicMock()

    context = ConnectionContext(connection)
    assert context.connection_handler
    assert not connection.is_transaction_running

    with context:
        mock.__enter__.assert_called()
        set_tr.assert_called_with(True)
    mock.__exit__.assert_called()
    set_tr.assert_called_with(False)


def test_get_connection_context(connection):
    connection.ensure_connection = ec = MagicMock()
    with patch(
        "shared.postgresql_backend.pg_connection_handler.ConnectionContext"
    ) as context:
        connection.get_connection_context()
        context.assert_called()
        ec.assert_called()


def test_get_connection_context_transaction_running(connection):
    connection.is_transaction_running = True
    with pytest.raises(BadCodingError):
        connection.get_connection_context()


def test_ensure_connection(connection):
    with patch("psycopg2.connect") as connect:
        connection.ensure_connection()
        connect.assert_called()


def test_ensure_connection_error(connection):
    connect = MagicMock()
    connect.side_effect = psycopg2.Error
    with patch("psycopg2.connect", new=connect):
        with pytest.raises(DatabaseError):
            connection.ensure_connection()


def test_ensure_connection_exists(connection):
    connection.connection = True
    with patch("psycopg2.connect") as connect:
        connection.ensure_connection()
        connect.assert_not_called()
    # TODO: adjust test when code is fixed


def test_to_json(connection):
    json = connection.to_json({"a": "a", "b": "b"})
    assert type(json) is Json
    assert str(json) == '\'{"a": "a", "b": "b"}\''


def test_get_connection_with_open_transaction(connection):
    connection.connection = mock = MagicMock()
    connection.is_transaction_running = True
    assert connection.get_connection_with_open_transaction() == mock


def test_get_connection_with_open_transaction_no_connection(connection):
    with pytest.raises(BadCodingError):
        connection.get_connection_with_open_transaction()


def test_get_connection_with_open_transaction_no_transaction(connection):
    connection.connection = MagicMock()
    with pytest.raises(BadCodingError):
        connection.get_connection_with_open_transaction()


def setup_mocked_connection(connection):
    cursor = MagicMock(name="cursor")
    cursor.execute = MagicMock(name="execute")
    cursor_context = MagicMock(name="cursor_context")
    cursor_context.__enter__ = MagicMock(return_value=cursor, name="enter")
    mock = MagicMock(name="connection_mock")
    mock.cursor = MagicMock(return_value=cursor_context, name="cursor_func")
    connection.get_connection_with_open_transaction = MagicMock(
        return_value=mock, name="gcwot"
    )
    return cursor


def test_execute(connection):
    cursor = setup_mocked_connection(connection)

    connection.execute(1, 2)
    connection.get_connection_with_open_transaction.assert_called()
    cursor.execute.assert_called_with(1, 2)


def test_query(connection):
    cursor = setup_mocked_connection(connection)
    result = MagicMock()
    cursor.fetchall = MagicMock(return_value=result)

    assert connection.query(1, 2) == result
    connection.get_connection_with_open_transaction.assert_called()
    cursor.execute.assert_called_with(1, 2)
    cursor.fetchall.assert_called()


def test_query_single_value(connection):
    cursor = setup_mocked_connection(connection)
    result = MagicMock()
    result[0] = MagicMock()
    cursor.fetchone = MagicMock(return_value=result)

    assert connection.query_single_value(1, 2) == result[0]
    connection.get_connection_with_open_transaction.assert_called()
    cursor.execute.assert_called_with(1, 2)
    cursor.fetchone.assert_called()


def test_query_single_value_none(connection):
    cursor = setup_mocked_connection(connection)
    cursor.fetchone = MagicMock(return_value=None)

    assert connection.query_single_value(1, 2) is None


def test_query_list_of_single_values(connection):
    connection.query = MagicMock()
    connection.query_list_of_single_values(1, 2)
    connection.query.assert_called_with(1, 2)


def test_shutdown(connection):
    connection.connection = mock = MagicMock()
    mock.close = close = MagicMock()
    connection.context = MagicMock()

    connection.shutdown()
    close.assert_called()
    assert connection.connection is None
    assert connection.context is None
