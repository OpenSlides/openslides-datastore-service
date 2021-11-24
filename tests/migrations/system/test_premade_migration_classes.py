from datastore.migrations import (
    AddFieldMigration,
    RenameFieldMigration,
    RemoveFieldMigration,
)


def test_rename_field(
    migration_handler,
    write,
    set_migration_index_to_1,
    assert_model,
    query_single_value,
    assert_finalized,
):
    """f -> f_new"""
    write({"type": "create", "fqid": "a/1", "fields": {"f": [1]}})
    write({"type": "create", "fqid": "b/1", "fields": {"f": [1]}})
    write({"type": "update", "fqid": "a/1", "fields": {"f": [2]}})
    write({"type": "update", "fqid": "a/1", "list_fields": {"add": {"f": [3]}}})
    write({"type": "update", "fqid": "a/1", "fields": {"f": None}})
    write({"type": "update", "fqid": "a/1", "fields": {"f": "Hello"}})
    set_migration_index_to_1()

    class RenameField(RenameFieldMigration):
        target_migration_index = 2
        collection = "a"
        old_field = "f"
        new_field = "f_new"

    migration_handler.register_migrations(RenameField)
    migration_handler.finalize()

    assert_finalized()
    assert_model(
        "a/1", {"f_new": [1], "meta_deleted": False, "meta_position": 1}, position=1
    )
    assert_model(
        "b/1", {"f": [1], "meta_deleted": False, "meta_position": 2}, position=2
    )
    assert_model(
        "a/1", {"f_new": [2], "meta_deleted": False, "meta_position": 3}, position=3
    )
    assert_model(
        "a/1", {"f_new": [2, 3], "meta_deleted": False, "meta_position": 4}, position=4
    )
    assert_model("a/1", {"meta_deleted": False, "meta_position": 5}, position=5)
    assert_model(
        "a/1", {"f_new": "Hello", "meta_deleted": False, "meta_position": 6}, position=6
    )


def test_add_field_with_default(
    migration_handler,
    write,
    set_migration_index_to_1,
    assert_model,
    query_single_value,
    assert_finalized,
):
    write({"type": "create", "fqid": "a/1", "fields": {"f": 3}})
    write({"type": "create", "fqid": "b/1", "fields": {"x": 42}})
    write({"type": "update", "fqid": "a/1", "fields": {"f": 5, "g": 127}})
    set_migration_index_to_1()

    class AddField(AddFieldMigration):
        target_migration_index = 2
        collection = "a"
        field = "g"
        default = "default"

    migration_handler.register_migrations(AddField)
    migration_handler.finalize()

    assert_finalized()
    assert_model(
        "a/1",
        {"f": 3, "g": "default", "meta_deleted": False, "meta_position": 1},
        position=1,
    )
    assert_model(
        "b/1", {"x": 42, "meta_deleted": False, "meta_position": 2}, position=2
    )
    assert_model(
        "a/1", {"f": 5, "g": 127, "meta_deleted": False, "meta_position": 3}, position=3
    )


def test_remove_field(
    migration_handler,
    write,
    set_migration_index_to_1,
    assert_model,
    query_single_value,
    assert_finalized,
):
    write({"type": "create", "fqid": "a/1", "fields": {"a": 5, "r": [3]}})
    write({"type": "update", "fqid": "a/1", "fields": {"a": 6, "r": [20]}})
    write({"type": "update", "fqid": "a/1", "fields": {"a": 6, "r": [20]}})
    write({"type": "update", "fqid": "a/1", "list_fields": {"add": {"r": [3]}, "remove": {"r": [20]}}})
    write({"type": "delete", "fqid": "a/1"})
    write({"type": "restore", "fqid": "a/1"})

    set_migration_index_to_1()

    class RemoveField(RemoveFieldMigration):
        target_migration_index = 2
        collection = "a"
        field = "r"

    migration_handler.register_migrations(RemoveField)
    migration_handler.finalize()

    assert_finalized()
    assert_model(
        "a/1",
        {"a": 5, "meta_deleted": False, "meta_position": 1},
        position=1,
    )
    assert_model("a/1", {"a": 6, "meta_deleted": False, "meta_position": 2}, position=2)
    assert_model("a/1", {"a": 6, "meta_deleted": False, "meta_position": 3}, position=3)
    assert_model("a/1", {"a": 6, "meta_deleted": False, "meta_position": 4}, position=4)
    assert_model("a/1", {"a": 6, "meta_deleted": True, "meta_position": 5}, position=5)
    assert_model("a/1", {"a": 6, "meta_deleted": False, "meta_position": 6}, position=6)