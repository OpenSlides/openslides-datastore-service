from unittest.mock import MagicMock

import pytest

from datastore.shared.di import injector
from datastore.shared.services import EnvironmentService, ShutdownService
from datastore.writer.redis_backend.connection_handler import ConnectionHandler
from datastore.writer.redis_backend.redis_connection_handler import (
    RedisConnectionHandlerService,
)
from tests import reset_di  # noqa


@pytest.fixture(autouse=True)
def provide_di(reset_di):  # noqa
    injector.register(ShutdownService, ShutdownService)
    injector.register(EnvironmentService, EnvironmentService)
    injector.register(ConnectionHandler, RedisConnectionHandlerService)
    yield


@pytest.fixture()
def connection(provide_di):
    yield injector.get(ConnectionHandler)


def test_xadd_empty_arguments(connection):
    connection.ensure_connection = ec = MagicMock()
    connection.xadd(None, None)
    ec.assert_not_called()


def test_shutdown(connection):
    connection.connection = c = MagicMock()
    connection.shutdown()

    c.close.assert_called()
    assert connection.connection is None
