from datastore.migrations.core.base_migrations import BaseModelMigration
from datastore.shared.di import service_as_factory
from datastore.shared.postgresql_backend import ConnectionHandler
from datastore.shared.services import ReadDatabase
from datastore.shared.util import BadCodingError
from datastore.writer.core import Database

from ..migration_logger import MigrationLogger
from .migrater import ModelMigrater


@service_as_factory
class ModelMigraterImplementation(ModelMigrater):
    read_database: ReadDatabase
    write_database: Database
    connection: ConnectionHandler
    logger: MigrationLogger

    def migrate(self) -> None:
        current_migration_index = self.read_database.get_current_migration_index()
        self.logger.info(
            f"Migrating models from MI {current_migration_index} to MI {self.target_migration_index} ..."
        )
        for source_migration_index in range(
            current_migration_index, self.target_migration_index
        ):
            target_migration_index = source_migration_index + 1
            self.logger.debug(
                f"\tRunning migration with target migration index {target_migration_index}"
            )
            migration = self.migrations[target_migration_index]
            if not isinstance(migration, BaseModelMigration):
                raise BadCodingError(
                    "Event migrater cannot execute non-event migrations"
                )

            with self.connection.get_connection_context():
                events = migration.migrate()
                if events:
                    self.write_database.insert_events(
                        events, target_migration_index, None, 0
                    )
