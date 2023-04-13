from typing import List, Optional

import pytest

from datastore.migrations import (
    BaseEvent,
    BaseEventMigration,
    CreateEvent,
    MismatchingMigrationIndicesException,
)
from datastore.shared.typing import Position


class TestInitialMigrationKeyframeModifier:
    meta_position: Position = 1

    def test_simple_migration(self, setup_memory_migration, migration_handler):
        data = [CreateEvent("a/1", {"f": 1})]

        class MyMigration(BaseEventMigration):
            target_migration_index = 2

            def migrate_event(
                inner_self,
                event: BaseEvent,
            ) -> Optional[List[BaseEvent]]:
                if event.fqid == "a/1":
                    event.data["f"] = 2
                return [event]

        migration_handler.register_migrations(MyMigration)
        migration_handler.migrater.set_additional_data(data, {}, 1)
        migration_handler.finalize()
        migrated_events = migration_handler.migrater.get_migrated_events()
        assert migrated_events[0].data["f"] == 2

    def test_mismatching_migration_index(
        self, setup_memory_migration, migration_handler
    ):
        data = [CreateEvent("a/1", {"f": 1})]

        class MyMigration(BaseEventMigration):
            target_migration_index = 2

            def migrate_event(
                inner_self,
                event: BaseEvent,
            ) -> Optional[List[BaseEvent]]:
                if event.fqid == "a/1":
                    event.data["f"] = 2
                return [event]

        migration_handler.register_migrations(MyMigration)
        migration_handler.migrater.set_additional_data(data, {}, 3)
        with pytest.raises(MismatchingMigrationIndicesException):
            migration_handler.finalize()
        migrated_events = migration_handler.migrater.get_migrated_events()
        assert migrated_events == []
