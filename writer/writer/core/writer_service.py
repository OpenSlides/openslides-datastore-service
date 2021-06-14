import threading
from collections import defaultdict
from typing import Dict, List, Set

from shared.di import service_as_factory
from shared.postgresql_backend import retry_on_db_failure
from shared.util import logger

from .database import Database
from .db_events import BaseDbEvent
from .event_executor import EventExecutor
from .event_translator import EventTranslator
from .messaging import Messaging
from .occ_locker import OccLocker
from .write_request import BaseRequestEvent, WriteRequest


@service_as_factory
class WriterService:

    _lock = threading.Lock()

    database: Database
    occ_locker: OccLocker
    event_translator: EventTranslator
    event_executor: EventExecutor
    messaging: Messaging

    @retry_on_db_failure
    def write(
        self,
        write_requests: List[WriteRequest],
        log_all_modified_fields: bool = True,
    ) -> None:
        self.write_requests = write_requests

        with self._lock:
            self.position_to_db_events = {}
            with self.database.get_context():
                for write_request in self.write_requests:
                    # Convert request events to db events
                    db_events = self.event_translator.translate(write_request.events)
                    position = self.write_with_database_context(
                        write_request, db_events
                    )
                    self.position_to_db_events[position] = db_events

            # Only propagate updates to redis after the transaction has finished
            self.messaging.handle_events(
                self.position_to_db_events,
                log_all_modified_fields=log_all_modified_fields,
            )

        self.print_stats()
        self.print_summary()

    def print_stats(self) -> None:
        stats: Dict[str, int] = defaultdict(int)
        for write_request in self.write_requests:
            for event in write_request.events:
                stats[self.get_request_name(event)] += 1
        stats_string = ", ".join(f"{cnt} {name}" for name, cnt in stats.items())
        logger.info(f"Events executed ({stats_string})")

    def print_summary(self) -> None:
        summary: Dict[str, Set[str]] = defaultdict(set)  # event type <-> set[fqid]
        for write_request in self.write_requests:
            for event in write_request.events:
                summary[self.get_request_name(event)].add(event.fqid)
        logger.info(
            "\n".join(
                f"{eventType}: {list(fqids)}" for eventType, fqids in summary.items()
            )
        )

    def get_request_name(self, event: BaseRequestEvent) -> str:
        return type(event).__name__.replace("Request", "").replace("Event", "").upper()

    def write_with_database_context(
        self, write_request: WriteRequest, db_events: List[BaseDbEvent]
    ) -> int:
        # Check locked_fields -> Possible LockedError
        self.occ_locker.assert_locked_fields(write_request)

        # Insert db events with position data
        position = self.database.insert_events(
            db_events, write_request.information, write_request.user_id
        )

        # Store updated models in the Read-DB
        self.event_executor.update(db_events, position)

        return position

    @retry_on_db_failure
    def reserve_ids(self, collection: str, amount: int) -> List[int]:
        with self.database.get_context():
            ids = self.database.reserve_next_ids(collection, amount)
            logger.info(f"{len(ids)} ids reserved")
            return ids

    @retry_on_db_failure
    def truncate_db(self) -> None:
        with self.database.get_context():
            self.database.truncate_db()
            logger.info("Database truncated")
