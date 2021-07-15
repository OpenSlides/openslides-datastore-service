from typing import ContextManager, Dict, List, Protocol, Tuple

from datastore.shared.di import service_interface
from datastore.shared.typing import JSON, Field, Fqid, Id, Position
from datastore.writer.core.write_request import BaseRequestEvent


@service_interface
class Database(Protocol):
    def get_context(self) -> ContextManager[None]:
        """
        Creates a new context to execute all actions inside
        """

    def insert_events(
        self,
        events: List[BaseRequestEvent],
        migration_index: int,
        information: JSON,
        user_id: int,
    ) -> Tuple[Position, Dict[Fqid, Dict[Field, JSON]]]:
        """
        Inserts the given events. This may raise ModelExists,
        ModelDoesNotExist or ModelNotDeleted. Returns the generated position and
        modified fqfields with values.
        """

    def reserve_next_ids(self, collection: str, amount: int) -> List[Id]:
        """
        Reserves next ids and returns the requested ids as a list.
        May Raises InvalidFormat, is collection is malformed or amount too high
        """

    def truncate_db(self) -> None:
        """Truncate all tables. Only for dev purposes!"""
