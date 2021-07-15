from typing import Dict, Protocol

from datastore.shared.di import service_interface
from datastore.shared.typing import JSON, Field, Fqid, Position


@service_interface
class Messaging(Protocol):
    def handle_events(
        self,
        events_per_position: Dict[Position, Dict[Fqid, Dict[Field, JSON]]],
        log_all_modified_fields: bool = True,
    ) -> None:
        """
        Should initiale all events to the message bus.
        """
