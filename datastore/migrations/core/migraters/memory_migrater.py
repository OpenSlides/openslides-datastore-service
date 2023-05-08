from typing import Dict

from datastore.shared.typing import Fqid, Model
from datastore.shared.util.key_strings import META_DELETED

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
    models: Dict[Fqid, Model]

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
        for model in models.values():
            model[META_DELETED] = False
        self.models = models
        self.start_migration_index = start_migration_index

    def get_migrated_models(self) -> Dict[Fqid, Model]:
        raise NotImplementedError()
