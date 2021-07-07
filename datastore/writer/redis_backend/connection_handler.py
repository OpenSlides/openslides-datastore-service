from typing import Dict, Protocol

from datastore.shared.di import service_interface


@service_interface
class ConnectionHandler(Protocol):
    def xadd(self, topic: str, fields: Dict[str, str]) -> None:
        """Adds the message onto the given stream with name topic"""
