from typing import Dict, List, Protocol

from datastore.shared.di import service_interface
from datastore.writer.core.db_events import BaseDbEvent


@service_interface
class Messaging(Protocol):
    def handle_events(
        self,
        events_per_position: Dict[int, List[BaseDbEvent]],
        log_all_modified_fields: bool = True,
    ) -> None:
        """
        Should initiale all events to the message bus.
        """
