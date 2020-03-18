from typing import List, Protocol

from shared.di import service_interface


@service_interface
class ConnectionHandler(Protocol):
    def xadd(self, topic: str, parts: List[str]) -> None:
        """ Adds the message onto the given stream with name topic """
