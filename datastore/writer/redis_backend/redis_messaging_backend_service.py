import json
from typing import Dict

from datastore.shared.di import service_as_singleton
from datastore.shared.typing import Fqfield
from datastore.shared.util import (
    JSON,
    META_POSITION,
    Field,
    Fqid,
    Position,
    fqfield_from_fqid_and_field,
    logger,
)
from datastore.writer.core import Messaging

from .connection_handler import ConnectionHandler

from opentelemetry.trace import get_current_span


MODIFIED_FIELDS_TOPIC = "ModifiedFields"


@service_as_singleton
class RedisMessagingBackendService(Messaging):

    connection: ConnectionHandler

    def handle_events(
        self,
        events_per_position: Dict[Position, Dict[Fqid, Dict[Field, JSON]]],
        log_all_modified_fields: bool = True,
    ) -> None:
        modified_fqfields = self.get_modified_fqfields(events_per_position)
        if log_all_modified_fields:
            logger.debug(
                f"written fqfields into {MODIFIED_FIELDS_TOPIC}: "
                + json.dumps(modified_fqfields)
            )

        span_context = get_current_span().get_span_context()
        trace_id_hex = span_context.trace_id.to_bytes(((span_context.trace_id.bit_length() + 7) // 8),"big").hex()
        span_id_hex = span_context.span_id.to_bytes((( span_context.span_id.bit_length() + 7) // 8),"big").hex()
        span_data = f"{trace_id_hex}:{span_id_hex}:{span_context.trace_flags}"
        modified_fqfields["span"] = span_data

        
        self.connection.xadd(MODIFIED_FIELDS_TOPIC, modified_fqfields)

    def get_modified_fqfields(
        self, events_per_position: Dict[Position, Dict[Fqid, Dict[Field, JSON]]]
    ) -> Dict[Fqfield, str]:
        modified_fqfields = {}
        for position, models in events_per_position.items():
            for fqid, fields in models.items():
                for field, value in fields.items():
                    fqfield = fqfield_from_fqid_and_field(fqid, field)
                    modified_fqfields[fqfield] = json.dumps(value)
                meta_position_fqfield = fqfield_from_fqid_and_field(fqid, META_POSITION)
                modified_fqfields[meta_position_fqfield] = str(position)
        return modified_fqfields
