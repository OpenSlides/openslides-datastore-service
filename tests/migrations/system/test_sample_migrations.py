from typing import List, Optional

from datastore.migrations import (
    BaseEvent,
    BaseMigration,
    CreateEvent,
    DeleteFieldsEvent,
    ListUpdateEvent,
    RestoreEvent,
    UpdateEvent,
)
from datastore.shared.util import (
    collection_and_id_from_fqid,
    fqid_from_collection_and_id,
)


class RenameField(BaseMigration):
    """f -> f_new"""

    target_migration_index = 2

    def modify(self, object):
        if "f" in object:
            object["f_new"] = object["f"]
            del object["f"]

    def migrate_event(
        self,
        event: BaseEvent,
    ) -> Optional[List[BaseEvent]]:
        if isinstance(event, CreateEvent) or isinstance(event, UpdateEvent):
            self.modify(event.data)

        if isinstance(event, DeleteFieldsEvent):
            if "f" in event.data:
                event.data.remove("f")
                event.data.append("f_new")

        if isinstance(event, ListUpdateEvent):
            self.modify(event.add)
            self.modify(event.remove)

        return [event]


def test_rename_field(
    migration_handler, write, assert_model, query_single_value, assert_finalized
):
    """f -> f_new"""
    write({"type": "create", "fqid": "a/1", "fields": {"f": [1]}})
    write({"type": "update", "fqid": "a/1", "fields": {"f": [2]}})
    write({"type": "update", "fqid": "a/1", "list_fields": {"add": {"f": [3]}}})
    write({"type": "update", "fqid": "a/1", "fields": {"f": None}})
    write({"type": "update", "fqid": "a/1", "fields": {"f": "Hello"}})

    migration_handler.register_migrations(RenameField)
    migration_handler.finalize()

    assert_finalized()
    assert_model(
        "a/1", {"f_new": [1], "meta_deleted": False, "meta_position": 1}, position=1
    )
    assert_model(
        "a/1", {"f_new": [2], "meta_deleted": False, "meta_position": 2}, position=2
    )
    assert_model(
        "a/1", {"f_new": [2, 3], "meta_deleted": False, "meta_position": 3}, position=3
    )
    assert_model("a/1", {"meta_deleted": False, "meta_position": 4}, position=4)
    assert_model(
        "a/1", {"f_new": "Hello", "meta_deleted": False, "meta_position": 5}, position=5
    )


def test_move_id(
    migration_handler,
    write,
    assert_model,
    exists_model,
    query_single_value,
    assert_finalized,
):
    """
    Move id->id+1: a/1 will be a/2 and a/2 will be a/3. This is fictive and (hopefully)
    not be needed in productive usage. Also note that values are not tested here. E.g.
    generic relations must also be adapted in productive usage.
    """
    write({"type": "create", "fqid": "a/1", "fields": {"f": [1]}})
    write(
        {"type": "update", "fqid": "a/1", "fields": {"f": [2]}},
        {"type": "create", "fqid": "a/2", "fields": {"f": 42}},
    )
    write({"type": "update", "fqid": "a/1", "list_fields": {"add": {"f": [3]}}})
    write({"type": "update", "fqid": "a/1", "fields": {"f": None}})
    write({"type": "delete", "fqid": "a/1"})
    write({"type": "restore", "fqid": "a/1"})

    class MoveId(BaseMigration):
        target_migration_index = 2

        def migrate_event(
            self,
            event: BaseEvent,
        ) -> Optional[List[BaseEvent]]:
            collection, id = collection_and_id_from_fqid(event.fqid)
            event.fqid = fqid_from_collection_and_id(collection, id + 1)
            return [event]

    migration_handler.register_migrations(MoveId)
    migration_handler.finalize()

    assert_finalized()

    assert_model(
        "a/2", {"f": [1], "meta_deleted": False, "meta_position": 1}, position=1
    )
    assert_model(
        "a/2", {"f": [2], "meta_deleted": False, "meta_position": 2}, position=2
    )
    assert_model(
        "a/2", {"f": [2, 3], "meta_deleted": False, "meta_position": 3}, position=3
    )
    assert_model("a/2", {"meta_deleted": False, "meta_position": 4}, position=4)
    assert_model("a/2", {"meta_deleted": True, "meta_position": 5}, position=5)
    assert_model("a/2", {"meta_deleted": False, "meta_position": 6}, position=6)

    assert not exists_model("a/3", position=1)
    assert_model(
        "a/3", {"f": 42, "meta_deleted": False, "meta_position": 2}, position=2
    )


def test_remove_field(
    migration_handler, write, assert_model, query_single_value, assert_finalized
):
    """remove f"""
    write({"type": "create", "fqid": "a/1", "fields": {"f": [1]}})
    write({"type": "update", "fqid": "a/1", "fields": {"f": [2]}})
    write({"type": "update", "fqid": "a/1", "list_fields": {"add": {"f": [3]}}})
    write({"type": "update", "fqid": "a/1", "fields": {"f": None}})
    write({"type": "update", "fqid": "a/1", "fields": {"f": "Hello"}})

    class RemoveField(BaseMigration):
        target_migration_index = 2

        def migrate_event(
            self,
            event: BaseEvent,
        ) -> Optional[List[BaseEvent]]:
            if isinstance(event, CreateEvent) or isinstance(event, UpdateEvent):
                event.data.pop("f", None)

            if isinstance(event, DeleteFieldsEvent):
                if "f" in event.data:
                    event.data.remove("f")

            if isinstance(event, ListUpdateEvent):
                event.add.pop("f", None)
                event.remove.pop("f", None)

            return [event]

    migration_handler.register_migrations(RemoveField)
    migration_handler.finalize()

    assert_finalized()
    assert_model("a/1", {"meta_deleted": False, "meta_position": 1}, position=1)
    assert_model("a/1", {"meta_deleted": False, "meta_position": 2}, position=2)
    assert_model("a/1", {"meta_deleted": False, "meta_position": 3}, position=3)
    assert_model("a/1", {"meta_deleted": False, "meta_position": 4}, position=4)
    assert_model("a/1", {"meta_deleted": False, "meta_position": 5}, position=5)


def test_add_required_field_based_on_migrated_data(
    migration_handler, write, assert_model, query_single_value, assert_finalized
):
    """First, rename f->f_new. Second migration adds `g`, which is f_new*2"""
    write({"type": "create", "fqid": "a/1", "fields": {"f": 3}})

    class AddField(BaseMigration):
        target_migration_index = 3

        def migrate_event(
            self,
            event: BaseEvent,
        ) -> Optional[List[BaseEvent]]:
            if isinstance(event, CreateEvent):
                event.data["g"] = event.data["f_new"] * 2
            return [event]

    migration_handler.register_migrations(RenameField, AddField)
    migration_handler.finalize()

    assert_finalized()
    assert_model("a/1", {"f_new": 3, "g": 6, "meta_deleted": False, "meta_position": 1})


def test_create_additional_model(
    migration_handler, write, assert_model, query_single_value, assert_finalized
):
    """Also a setup-for-tests scenario here."""
    write({"type": "create", "fqid": "config/1", "fields": {"create_b": True}})
    write({"type": "create", "fqid": "a/1", "fields": {}})

    class CreateModel(BaseMigration):
        target_migration_index = 2

        def migrate_event(
            self,
            event: BaseEvent,
        ) -> Optional[List[BaseEvent]]:
            if isinstance(event, CreateEvent) and event.fqid == "a/1":
                config = self.new_accessor.get_model("config/1")
                if config["create_b"]:
                    return [event, CreateEvent("b/1", {})]
            return None

    migration_handler.register_migrations(CreateModel)
    migration_handler.finalize()

    assert_finalized()
    assert_model("b/1", {"meta_deleted": False, "meta_position": 2})


def test_access_field_after_rename(
    migration_handler, write, assert_model, query_single_value, assert_finalized
):
    """First rename f->f_new. In a second migration access both fields via both accessors"""
    write({"type": "create", "fqid": "a/1", "fields": {"f": [1]}})
    write({"type": "update", "fqid": "a/1", "fields": {"f": [2]}})
    write({"type": "update", "fqid": "a/1", "list_fields": {"add": {"f": [3]}}})
    write({"type": "update", "fqid": "a/1", "fields": {"f": "Hello"}})
    write({"type": "delete", "fqid": "a/1"})
    write({"type": "restore", "fqid": "a/1"})

    class RenameMigration(RenameField):
        target_migration_index = 2

        def migrate_event(
            self,
            event: BaseEvent,
        ) -> Optional[List[BaseEvent]]:
            events = super().migrate_event(event)

            if not isinstance(event, CreateEvent) and not isinstance(
                event, RestoreEvent
            ):
                old = self.old_accessor.get_model("a/1")
                new = self.new_accessor.get_model("a/1")
                assert "f" in old
                assert "f_new" in new
                assert old["f"] == new["f_new"]
            return events

    migration_handler.register_migrations(RenameMigration)
    migration_handler.finalize()

    assert_finalized()
    assert_model(
        "a/1", {"f_new": [1], "meta_deleted": False, "meta_position": 1}, position=1
    )
    assert_model(
        "a/1", {"f_new": [2], "meta_deleted": False, "meta_position": 2}, position=2
    )
    assert_model(
        "a/1", {"f_new": [2, 3], "meta_deleted": False, "meta_position": 3}, position=3
    )
    assert_model(
        "a/1", {"f_new": "Hello", "meta_deleted": False, "meta_position": 4}, position=4
    )
    assert_model(
        "a/1", {"f_new": "Hello", "meta_deleted": True, "meta_position": 5}, position=5
    )
    assert_model(
        "a/1", {"f_new": "Hello", "meta_deleted": False, "meta_position": 6}, position=6
    )
