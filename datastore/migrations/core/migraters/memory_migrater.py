from typing import Dict, List

from datastore.shared.typing import Fqid, Model

from ..events import BaseEvent
from ..exceptions import MismatchingMigrationIndicesException
from .migrater import BaseMigrater


class MemoryMigrater(BaseMigrater):
    """
    This migrater is made for in memory migrations of meeting imports.
    The whole import will be imported to 1 position. Unlike the database
    migration, there is no need to have keyframes/baselines for all
    migrationlevels for the last position.
    """

    start_migration_index: int
    imported_models: Dict[Fqid, Model]
    migrated_events: List[BaseEvent]

    def check_migration_index(self) -> None:
        if (
            self.start_migration_index < 1
            or self.start_migration_index > self.target_migration_index
        ):
            raise MismatchingMigrationIndicesException(
                "The migration index of import data is invalid: "
                + f"Given migration index of import data: {self.start_migration_index} "
                + f"Current backend migration index: {self.target_migration_index}"
            )

    def set_import_data(
        self,
        models: Dict[Fqid, Model],
        start_migration_index: int,
    ) -> None:
        self.imported_models = models
        self.start_migration_index = start_migration_index
        self.migrated_events = []

    def get_migrated_events(self) -> List[BaseEvent]:
        return self.migrated_events
