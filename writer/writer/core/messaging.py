from typing import List, Protocol

from writer.di import service_interface

from .db_events import BaseDbEvent


@service_interface
class Messaging(Protocol):
    def handle_events(self, events: List[BaseDbEvent], position: int) -> None:
        """
        Should initiale all events to the message bus.
        """
