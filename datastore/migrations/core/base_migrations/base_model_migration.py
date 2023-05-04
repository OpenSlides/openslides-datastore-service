from typing import List, Optional

from datastore.migrations.core.migration_reader import MigrationReader
from datastore.writer.core import BaseRequestEvent

from .base_migration import BaseMigration


class BaseModelMigration(BaseMigration):
    """The base class to represent a model migration."""

    reader: MigrationReader

    def migrate(self, reader: MigrationReader) -> Optional[List[BaseRequestEvent]]:
        self.reader = reader
        return self.migrate_models()

    def migrate_models(self) -> Optional[List[BaseRequestEvent]]:
        """
        Migrates the models. The current models can be accessed via self.database. Should return
        a list of events with all changes to apply.
        """
