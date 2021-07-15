from unittest.mock import MagicMock, patch

import pytest

from datastore.migrations.migration_logger import (
    MigrationLogger,
    MigrationLoggerImplementation,
)
from datastore.shared.di import injector
from tests import reset_di  # noqa


@pytest.fixture()
def migration_logger(reset_di):  # noqa
    injector.register_as_singleton(MigrationLogger, MigrationLoggerImplementation)
    yield injector.get(MigrationLogger)


def test_print_info(migration_logger):
    message = MagicMock()
    with patch("builtins.print") as print_patch:
        migration_logger.info(message)
    print_patch.assert_called_with(message)


def test_print_debug_verbose(migration_logger):
    migration_logger.set_verbose(True)
    message = MagicMock()
    with patch("builtins.print") as print_patch:
        migration_logger.debug(message)
    print_patch.assert_called_with(message)


def test_print_debug_not_verbose(migration_logger):
    migration_logger.set_verbose(False)
    message = MagicMock()
    with patch("builtins.print") as print_patch:
        migration_logger.debug(message)
    print_patch.assert_not_called()
