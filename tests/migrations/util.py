from typing import List, Optional, Tuple
from unittest.mock import MagicMock

from datastore.migrations import BaseEvent, BaseEventMigration, BaseModelMigration
from datastore.writer.core import BaseRequestEvent


class LogMock(MagicMock):
    @property
    def output(self) -> Tuple[str, ...]:
        return tuple(c[0][0] for c in self.call_args_list)


def get_noop_event_migration(target_migration_index: Optional[int]):
    class NoopMigration(BaseEventMigration):
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


def get_lambda_event_migration(fn, target_migration_index=2):
    class LambdaMigration(BaseEventMigration):
        def __init__(self):
            self.target_migration_index = target_migration_index
            super().__init__()

        def migrate_event(
            self,
            event: BaseEvent,
        ) -> Optional[List[BaseEvent]]:
            return fn(event)

    return LambdaMigration


def get_noop_model_migration(target_migration_index: Optional[int]):
    class NoopMigration(BaseModelMigration):
        def __init__(self):
            if target_migration_index is not None:
                self.target_migration_index = target_migration_index
            super().__init__()

    return NoopMigration


def get_static_model_migration(events, target_migration_index=2):
    class StaticMigration(BaseModelMigration):
        def __init__(self):
            self.target_migration_index = target_migration_index
            super().__init__()

        def migrate(self) -> Optional[List[BaseRequestEvent]]:
            return events

    return StaticMigration
