from typing import List

from shared.di import service_as_singleton
from shared.util import META_POSITION, fqfield_from_fqid_and_field
from writer.core import Messaging
from writer.core.db_events import BaseDbEvent

from .connection_handler import ConnectionHandler


MODIFIED_FIELDS_TOPIC = "ModifiedFields"


@service_as_singleton
class RedisMessagingBackendService(Messaging):

    connection: ConnectionHandler

    def handle_events(self, events: List[BaseDbEvent], position: int) -> None:
        modified_fqfields = self.get_modified_fqfields(events, position)
        self.send_modified_fields_event(modified_fqfields)

    def get_modified_fqfields(
        self, events: List[BaseDbEvent], position: int
    ) -> List[str]:
        modified_fqfields = set()
        for event in events:
            fqfields = self.get_modified_fqfields_from_event(event)
            modified_fqfields.update(fqfields)
            meta_position_fqfield = fqfield_from_fqid_and_field(
                event.fqid, META_POSITION
            )
            modified_fqfields.add(meta_position_fqfield)
        return list(modified_fqfields)

    def get_modified_fqfields_from_event(self, event: BaseDbEvent) -> List[str]:
        return [
            fqfield_from_fqid_and_field(event.fqid, field)
            for field in event.get_modified_fields()
        ]

    def send_modified_fields_event(self, modified_fqfields: List[str]) -> None:
        parts = []
        for fqfield in modified_fqfields:
            parts.append("modified")
            parts.append(fqfield)
        self.connection.xadd(MODIFIED_FIELDS_TOPIC, parts)
