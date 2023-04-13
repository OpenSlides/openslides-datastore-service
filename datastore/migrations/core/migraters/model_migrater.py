from datastore.shared.di import service_as_factory
from datastore.shared.postgresql_backend import ConnectionHandler
from datastore.shared.services import ReadDatabase

from ..migration_logger import MigrationLogger
from .migrater import ModelMigrater


@service_as_factory
class ModelMigraterImplementation(ModelMigrater):
    read_database: ReadDatabase
    connection: ConnectionHandler
    logger: MigrationLogger

    def migrate(self) -> bool:
        return False
