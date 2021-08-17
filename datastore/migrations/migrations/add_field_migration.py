from typing import List, Optional

from datastore.shared.typing import JSON
from datastore.shared.util import collection_from_fqid

from .. import BaseEvent, BaseMigration, CreateEvent


class AddFieldMigration(BaseMigration):
    """
    This migration adds a new field to a collection with a given default value.
    """

    collection: str
    field: str
    default: JSON

    def migrate_event(
        self,
        event: BaseEvent,
    ) -> Optional[List[BaseEvent]]:
        collection = collection_from_fqid(event.fqid)
        if collection == self.collection and isinstance(event, CreateEvent):
            event.data[self.field] = self.default
            return [event]
        else:
            return None
