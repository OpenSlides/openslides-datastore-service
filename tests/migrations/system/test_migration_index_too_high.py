from unittest.mock import MagicMock

import pytest

from datastore.migrations import MismatchingMigrationIndicesException

from ..util import get_noop_migration


def test_migration_index_too_high_migrate(migration_handler, write, query_single_value):
    write({"type": "create", "fqid": "a/1", "fields": {}})
    migration_handler.register_migrations(get_noop_migration(2), get_noop_migration(3))
    migration_handler.migrate()

    migration_handler.run_migrations = rm = MagicMock()
    migration_handler.migrations_by_target_migration_index = {}
    migration_handler.register_migrations(
        get_noop_migration(2)
    )  # One migration too few

    with pytest.raises(MismatchingMigrationIndicesException):
        migration_handler.migrate()

    rm.assert_not_called()


def test_migration_index_too_high_finalize(
    migration_handler, write, query_single_value
):
    write({"type": "create", "fqid": "a/1", "fields": {}})
    migration_handler.register_migrations(get_noop_migration(2), get_noop_migration(3))
    migration_handler.finalize()

    migration_handler.run_migrations = rm = MagicMock()
    migration_handler.migrations_by_target_migration_index = {}
    migration_handler.register_migrations(
        get_noop_migration(2)
    )  # One migration too few

    with pytest.raises(MismatchingMigrationIndicesException):
        migration_handler.finalize()

    rm.assert_not_called()


def test_migration_index_too_high_reset(migration_handler, write, query_single_value):
    write({"type": "create", "fqid": "a/1", "fields": {}})
    migration_handler.register_migrations(get_noop_migration(2), get_noop_migration(3))
    migration_handler.finalize()

    migration_handler._delete_migration_keyframes = dmk = MagicMock()
    migration_handler.migrations_by_target_migration_index = {}
    migration_handler.register_migrations(
        get_noop_migration(2)
    )  # One migration too few

    with pytest.raises(MismatchingMigrationIndicesException):
        migration_handler.reset()

    dmk.assert_not_called()
