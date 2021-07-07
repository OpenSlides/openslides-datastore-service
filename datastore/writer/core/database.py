from typing import ContextManager, List, Protocol

from datastore.shared.di import service_interface
from datastore.shared.typing import JSON
from datastore.writer.core.db_events import BaseDbEvent


@service_interface
class Database(Protocol):
    def get_context(self) -> ContextManager[None]:
        """
        Creates a new context to execute all actions inside
        """

    def insert_events(
        self, events: List[BaseDbEvent], information: JSON, user_id: int
    ) -> int:
        """
        Inserts the given events. This may raise ModelExists,
        ModelDoesNotExist or ModelNotDeleted. Returns the generated position.
        """

    def reserve_next_ids(self, collection: str, amount: int) -> List[int]:
        """
        Reserves next ids and returns the requested ids as a list.
        May Raises InvalidFormat, is collection is malformed or amount too high
        """

    def truncate_db(self) -> None:
        """Truncate all tables. Only for dev purposes!"""
