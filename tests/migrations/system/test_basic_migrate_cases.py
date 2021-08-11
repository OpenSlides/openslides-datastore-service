from unittest.mock import MagicMock

import pytest

from datastore.migrations import MismatchingMigrationIndicesException
from datastore.migrations.migrater import Migrater
from datastore.shared.di import injector

from ..util import get_noop_migration


def test_no_migrations_to_apply(
    migration_handler,
    write,
):
    write({"type": "create", "fqid": "a/1", "fields": {}})

    migration_handler.register_migrations(get_noop_migration(2))
    migration_handler.finalize()

    migration_handler.logger.info = i = MagicMock()
    migration_handler.migrate()

    i.assert_called()
    assert (
        "No migrations to apply. The productive database is up to date."
        in i.call_args[0][0]
    )


def test_finalizing_needed(
    migration_handler,
    write,
):
    write({"type": "create", "fqid": "a/1", "fields": {}})

    migration_handler.register_migrations(get_noop_migration(2))
    migration_handler.migrate()

    migration_handler.logger.info = i = MagicMock()
    migration_handler.migrate()

    i.assert_called()
    assert (
        "No migrations to apply, but finalizing is still needed."
        in i.call_args_list[1][0][0]
    )
    assert "Done. Finalizing is still be needed." in i.call_args_list[2][0][0]


def test_finalizing_not_needed(
    migration_handler,
    write,
):
    write({"type": "create", "fqid": "a/1", "fields": {}})

    migration_handler.register_migrations(get_noop_migration(2))
    migration_handler.finalize()

    migration_handler.logger.info = i = MagicMock()
    migration_handler.finalize()

    i.assert_called()
    assert (
        "No migrations to apply. The productive database is up to date."
        in i.call_args[0][0]
    )


def test_invalid_migration_index(
    write,
    connection_handler,
):
    write({"type": "create", "fqid": "a/1", "fields": {}})

    with connection_handler.get_connection_context():
        connection_handler.execute(
            "update positions set migration_index=%s",
            [-1],
        )

    migrater = injector.get(Migrater)

    with pytest.raises(MismatchingMigrationIndicesException) as e:
        migrater.migrate(2, get_noop_migration(2)())

    assert (
        str(e.value)
        == "Datastore has an invalid migration index: MI of positions table=-1; MI of migrations_position table=1"
    )


def test_raising_migration_index(
    migration_handler,
    write,
    connection_handler,
):
    write({"type": "create", "fqid": "a/1", "fields": {}})
    write({"type": "create", "fqid": "a/2", "fields": {}})

    with connection_handler.get_connection_context():
        connection_handler.execute(
            "update positions set migration_index=1 where position=1",
            [],
        )
        connection_handler.execute(
            "update positions set migration_index=2 where position=2",
            [],
        )

    migration_handler.register_migrations(get_noop_migration(2), get_noop_migration(3))

    with pytest.raises(MismatchingMigrationIndicesException) as e:
        migration_handler.migrate()

    assert (
        str(e.value)
        == "Position 2 has a higher migration index as it's predecessor (position 1)"
    )
