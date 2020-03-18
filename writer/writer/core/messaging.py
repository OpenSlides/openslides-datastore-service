from typing import List, Protocol

from shared.di import service_interface
from writer.core.db_events import BaseDbEvent


@service_interface
class Messaging(Protocol):
    def handle_events(self, events: List[BaseDbEvent], position: int) -> None:
        """
        Should initiale all events to the message bus.
        """
