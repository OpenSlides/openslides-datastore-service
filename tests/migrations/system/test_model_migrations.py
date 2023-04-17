from datastore.writer.core import RequestCreateEvent
from tests.migrations.util import LogMock, get_static_model_migration


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
