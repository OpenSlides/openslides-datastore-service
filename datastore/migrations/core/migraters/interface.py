from typing import Dict, Protocol

from datastore.shared.di import service_interface

from ..base_migrations import BaseMigration


class Migrater(Protocol):
    def migrate(
        self,
        target_migration_index: int,
        migrations: Dict[int, BaseMigration],
    ) -> bool:
        """
        Runs the actual migrations of the datastore up to the target migration index.
        Returns true, if finalizing is needed.
        """


@service_interface
class EventMigrater(Migrater):
    """Marker class for an event migrater."""


@service_interface
class ModelMigrater(Migrater):
    """Marker class for a model migrater."""
