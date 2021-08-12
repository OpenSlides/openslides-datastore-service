from typing import List, Optional

from datastore.migrations import BaseEvent, BaseMigration


def get_noop_migration(target_migration_index: Optional[int]):
    class NoopMigration(BaseMigration):
        def __init__(self):
            if target_migration_index is not None:
                self.target_migration_index = target_migration_index
            super().__init__()

        def migrate_event(
            self,
            event: BaseEvent,
        ) -> Optional[List[BaseEvent]]:
            return None

    return NoopMigration


def get_lambda_migration(fn, target_migration_index=2):
    class LambdaMigration(BaseMigration):
        def __init__(self):
            self.target_migration_index = target_migration_index
            super().__init__()

        def migrate_event(
            self,
            event: BaseEvent,
        ) -> Optional[List[BaseEvent]]:
            return fn(event)

    return LambdaMigration
