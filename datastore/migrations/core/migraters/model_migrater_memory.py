from datastore.migrations.core.migration_reader import (
    MigrationReaderImplementationMemory,
)
from datastore.shared.di import service_as_factory
from datastore.shared.postgresql_backend import ConnectionHandler
from datastore.writer.core import Database

from ..migration_logger import MigrationLogger
from .memory_migrater import MemoryMigrater
from .migrater import ModelMigrater


@service_as_factory
class ModelMigraterImplementationMemory(ModelMigrater, MemoryMigrater):
    reader: MigrationReaderImplementationMemory
    write_database: Database
    connection: ConnectionHandler
    logger: MigrationLogger

    def migrate(self) -> None:
        self.check_migration_index()
        self.reader.models = self.imported_models

        self.logger.info(
            f"Migrate import data from MI {self.start_migration_index} to MI {self.target_migration_index} ..."
        )

        self.migrated_events = []
        for (
            source_migration_index,
            target_migration_index,
            migration,
        ) in self.get_migrations(self.start_migration_index):
            events = migration.migrate(self.reader)
            if events:
                # TODO: migrated events type mismatch
                self.migrated_events.extend(events)
