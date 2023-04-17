from typing import List, Optional

from datastore.writer.core import BaseRequestEvent

from .base_migration import BaseMigration


class BaseModelMigration(BaseMigration):
    """The base class to represent a model migration."""

    def migrate(self) -> Optional[List[BaseRequestEvent]]:
        """
        Migrates the models. The current models can be accessed via the read database. Should return
        a list of events with all changes to apply.
        """
