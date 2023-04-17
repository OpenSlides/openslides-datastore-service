from typing import Dict, Protocol

from datastore.shared.di import service_interface

from ..base_migrations import BaseMigration


class BaseMigrater(Protocol):
    target_migration_index: int
    migrations: Dict[int, BaseMigration]

    def init(
        self,
        target_migration_index: int,
        migrations: Dict[int, BaseMigration],
    ) -> None:
        self.target_migration_index = target_migration_index
        self.migrations = migrations

    def migrate(self) -> None:
        """
        Runs the actual migrations of the datastore up to the target migration index.
        """


@service_interface
class EventMigrater(BaseMigrater):
    """Marker class for an event migrater."""


@service_interface
class ModelMigrater(BaseMigrater):
    """Marker class for a model migrater."""
