from typing import Dict, List, Optional, Union

from datastore.shared.typing import JSON
from datastore.shared.util import collection_from_fqid

from .. import BaseEvent, BaseMigration, CreateEvent


class Calculated:
    """Marker class to indicate that a field should be calculated."""


class AddFieldsMigration(BaseMigration):
    """
    This migration adds new fields to multiple collections with given default values.
    """

    defaults: Dict[str, Dict[str, Union[JSON, Calculated]]]

    def migrate_event(
        self,
        event: BaseEvent,
    ) -> Optional[List[BaseEvent]]:
        if isinstance(event, CreateEvent):
            event_collection = collection_from_fqid(event.fqid)
            for collection, fields in self.defaults.items():
                if collection == event_collection:
                    for field, default in fields.items():
                        if isinstance(default, Calculated):
                            event.data[field] = self.get_default_for_field(event, field)
                        else:
                            event.data[field] = default
        return [event]

    def get_default_for_field(self, event: BaseEvent, field: str) -> JSON:
        """Can be overwritten for custom default values."""
        raise NotImplementedError()
