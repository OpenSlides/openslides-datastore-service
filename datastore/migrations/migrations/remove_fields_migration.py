from typing import Any, Dict, List, Optional

from datastore.shared.util import collection_from_fqid

from .. import (
    BaseEvent,
    BaseEventMigration,
    CreateEvent,
    DeleteFieldsEvent,
    ListUpdateEvent,
    UpdateEvent,
)


class RemoveFieldsMigration(BaseEventMigration):
    """
    This migration removes a field from all events for one collection.
    """

    collection_fields_map: Dict[str, List[str]]

    def remove_fields(self, obj: Dict[str, Any], fields: List[str]) -> None:
        for field in fields:
            if field in obj:
                del obj[field]

    def migrate_event(
        self,
        event: BaseEvent,
    ) -> Optional[List[BaseEvent]]:
        collection = collection_from_fqid(event.fqid)
        if collection not in self.collection_fields_map:
            return None
        fields = self.collection_fields_map[collection]

        if isinstance(event, CreateEvent) or isinstance(event, UpdateEvent):
            self.remove_fields(event.data, fields)

        elif isinstance(event, DeleteFieldsEvent):
            for field in fields:
                if field in event.data:
                    event.data.remove(field)

        elif isinstance(event, ListUpdateEvent):
            self.remove_fields(event.add, fields)
            self.remove_fields(event.remove, fields)

        return [event]
