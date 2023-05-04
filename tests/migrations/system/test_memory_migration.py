from typing import List, Optional

import pytest

from datastore.migrations import (
    BaseEvent,
    BaseEventMigration,
    CreateEvent,
    MismatchingMigrationIndicesException,
    setup,
)
from datastore.migrations.core.migration_handler import (
    MigrationHandlerImplementationMemory,
)
from datastore.writer.core.write_request import RequestUpdateEvent
from tests.migrations.util import get_lambda_model_migration


class TestInMemoryMigration:
    @pytest.fixture(autouse=True)
    def setup_memory_migration(reset_di):
        setup(memory_only=True)

    def test_simple_migration(self, migration_handler):
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
        migration_handler.event_migrater.set_additional_data(data, {}, 1)
        migration_handler.finalize()
        migrated_events = migration_handler.event_migrater.get_migrated_events()
        assert migrated_events[0].data["f"] == 2

    def test_mismatching_migration_index(self, migration_handler):
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
        migration_handler.event_migrater.set_additional_data(data, {}, 3)
        with pytest.raises(MismatchingMigrationIndicesException):
            migration_handler.finalize()
        migrated_events = migration_handler.event_migrater.get_migrated_events()
        assert migrated_events == []

    def test_model_migration(
        self, migration_handler: MigrationHandlerImplementationMemory
    ):
        data = {"a/1": {"f": 1}}

        migration_handler.register_migrations(
            get_lambda_model_migration(lambda _: [RequestUpdateEvent("a/1", {"f": 2})])
        )
        migration_handler.set_import_data(data, 1)
        migration_handler.finalize()
        migrated_events = migration_handler.event_migrater.get_migrated_events()
        assert len(migrated_events) == 2
        assert migrated_events[0].data["f"] == 1
        assert migrated_events[1].data["f"] == 2
