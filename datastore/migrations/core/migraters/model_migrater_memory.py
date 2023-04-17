from datastore.shared.di import service_as_factory
from datastore.shared.postgresql_backend import ConnectionHandler
from datastore.shared.services import ReadDatabase
from datastore.writer.core import Database

from ..migration_logger import MigrationLogger
from .migrater import ModelMigrater


@service_as_factory
class ModelMigraterImplementationMemory(ModelMigrater):
    read_database: ReadDatabase
    write_database: Database
    connection: ConnectionHandler
    logger: MigrationLogger

    def migrate(self) -> None:
        pass
