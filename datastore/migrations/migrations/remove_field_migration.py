from typing import Any, Dict, List, Optional

from datastore.shared.util import collection_from_fqid

from .. import (
    BaseEvent,
    BaseMigration,
    CreateEvent,
    DeleteFieldsEvent,
    ListUpdateEvent,
    UpdateEvent,
)


class RemoveFieldMigration(BaseMigration):
    """
    This migration removes a field from all events for one collection.
    """

    collection: str
    field: str

    def remove_field(self, object: Dict[str, Any]) -> None:
        if self.field in object:
            del object[self.field]

    def migrate_event(
        self,
        event: BaseEvent,
    ) -> Optional[List[BaseEvent]]:
        collection = collection_from_fqid(event.fqid)
        if collection != self.collection:
            return None

        if isinstance(event, CreateEvent) or isinstance(event, UpdateEvent):
            self.remove_field(event.data)

        elif isinstance(event, DeleteFieldsEvent):
            if self.field in event.data:
                event.data.remove(self.field)

        elif isinstance(event, ListUpdateEvent):
            self.remove_field(event.add)
            self.remove_field(event.remove)

        return [event]
