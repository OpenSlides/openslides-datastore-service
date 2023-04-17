from datastore.migrations.core.events import CreateEvent
from datastore.writer.core import RequestCreateEvent
from tests.migrations.util import (
    LogMock,
    get_lambda_event_migration,
    get_static_model_migration,
)


def test_model_migration(
    migration_handler, write, set_migration_index_to_1, assert_finalized, assert_model
):
    write({"type": "create", "fqid": "a/1", "fields": {}})
    set_migration_index_to_1()

    migration_handler.register_migrations(
        get_static_model_migration([RequestCreateEvent("a/2", {"f": 1})])
    )
    migration_handler.logger.info = i = LogMock()
    migration_handler.migrate()

    assert i.output == (
        "Running migrations.",
        "No event migrations to apply.",
        "1 model migration to apply.",
        "Current migration index: 1",
        "Done. Finalizing is still needed.",
    )

    i.reset_mock()
    migration_handler.finalize()

    assert i.output == (
        "Finalize migrations.",
        "No event migrations to apply.",
        "1 model migration to apply.",
        "Current migration index: 1",
        "Migrating models from MI 1 to MI 2 ...",
        "Cleaning collectionfield helper tables...",
        "Set the new migration index to 2...",
        "Done.",
    )
    assert_finalized(2)
    assert_model("a/2", {"f": 1, "meta_deleted": False, "meta_position": 2}, position=2)


def test_model_migration_no_events(
    migration_handler, write, set_migration_index_to_1, assert_finalized, assert_model
):
    write({"type": "create", "fqid": "a/1", "fields": {}})
    set_migration_index_to_1()

    migration_handler.register_migrations(get_static_model_migration(None))
    migration_handler.logger.info = i = LogMock()
    migration_handler.finalize()

    assert i.output == (
        "Finalize migrations.",
        "No event migrations to apply.",
        "1 model migration to apply.",
        "Current migration index: 1",
        "Migrating models from MI 1 to MI 2 ...",
        "Cleaning collectionfield helper tables...",
        "Set the new migration index to 2...",
        "Done.",
    )
    assert_finalized(2)


def test_model_migration_after_event_migration(
    migration_handler, write, set_migration_index_to_1, assert_finalized, assert_model
):
    write({"type": "create", "fqid": "a/1", "fields": {}})
    set_migration_index_to_1()

    migration_handler.register_migrations(
        get_lambda_event_migration(lambda e: [CreateEvent("a/1", {"f": 1})]),
        get_static_model_migration([RequestCreateEvent("a/2", {"f": 1})], 3),
    )
    migration_handler.logger.info = i = LogMock()
    migration_handler.migrate()

    assert i.output == (
        "Running migrations.",
        "1 event migration to apply.",
        "1 model migration to apply.",
        "Current migration index: 1",
        "Position 1 from MI 1 to MI 2 ...",
        "Done. Finalizing is still needed.",
    )

    i.reset_mock()
    migration_handler.finalize()

    assert i.output == (
        "Finalize migrations.",
        "No event migrations to apply, but finalizing is still needed.",
        "1 model migration to apply.",
        "Current migration index: 1",
        "Cleaning collectionfield helper tables...",
        "Calculate helper tables...",
        "Deleting all migration keyframes...",
        "Swap events and migration_events tables...",
        "Set the new migration index to 2...",
        "Clean up migration data...",
        "Migrating models from MI 2 to MI 3 ...",
        "Cleaning collectionfield helper tables...",
        "Set the new migration index to 3...",
        "Done.",
    )

    assert_finalized(3)
    assert_model("a/1", {"f": 1, "meta_deleted": False, "meta_position": 1}, position=1)
    assert_model("a/2", {"f": 1, "meta_deleted": False, "meta_position": 2}, position=2)
