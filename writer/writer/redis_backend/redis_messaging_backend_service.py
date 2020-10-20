import json
from typing import Dict, List

from shared.di import service_as_singleton
from shared.util import META_POSITION, fqfield_from_fqid_and_field, logger
from writer.core import Messaging
from writer.core.db_events import BaseDbEvent

from .connection_handler import ConnectionHandler


MODIFIED_FIELDS_TOPIC = "ModifiedFields"


@service_as_singleton
class RedisMessagingBackendService(Messaging):

    connection: ConnectionHandler

    def handle_events(
        self,
        events: List[BaseDbEvent],
        position: int,
        log_all_modified_fields: bool = True,
    ) -> None:
        modified_fqfields = self.get_modified_fqfields(events, position)
        if log_all_modified_fields:
            logger.debug(
                f"written fqfields into {MODIFIED_FIELDS_TOPIC}: "
                + json.dumps(modified_fqfields)
            )
        self.connection.xadd(MODIFIED_FIELDS_TOPIC, modified_fqfields)

    def get_modified_fqfields(
        self, events: List[BaseDbEvent], position: int
    ) -> Dict[str, str]:
        modified_fqfields = {}
        for event in events:
            fqfields = self.get_modified_fqfields_from_event(event)
            modified_fqfields.update(fqfields)
            meta_position_fqfield = fqfield_from_fqid_and_field(
                event.fqid, META_POSITION
            )
            modified_fqfields[meta_position_fqfield] = str(position)
        return modified_fqfields

    def get_modified_fqfields_from_event(self, event: BaseDbEvent) -> Dict[str, str]:
        return {
            fqfield_from_fqid_and_field(event.fqid, field): json.dumps(value)
            for field, value in event.get_modified_fields().items()
        }
