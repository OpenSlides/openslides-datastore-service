import threading
from collections import defaultdict
from typing import Dict, List, Optional, Set, Tuple

from datastore.shared.di import service_as_factory
from datastore.shared.postgresql_backend import retry_on_db_failure
from datastore.shared.services import ReadDatabase
from datastore.shared.typing import JSON, Field, Fqid
from datastore.shared.util import logger

from .database import Database
from .messaging import Messaging
from .occ_locker import OccLocker
from .write_request import BaseRequestEvent, WriteRequest


@service_as_factory
class WriterService:

    _lock = threading.Lock()

    database: Database
    read_database: ReadDatabase
    occ_locker: OccLocker
    messaging: Messaging

    @retry_on_db_failure
    def write(
        self,
        write_requests: List[WriteRequest],
        log_all_modified_fields: bool = True,
        migration_index: Optional[int] = None,
    ) -> None:
        self.write_requests = write_requests

        with self._lock:
            self.position_to_modified_models = {}
            with self.database.get_context():
                for write_request in self.write_requests:
                    position, modified_models = self.write_with_database_context(
                        write_request, migration_index=migration_index
                    )
                    self.position_to_modified_models[position] = modified_models

            # Only propagate updates to redis after the transaction has finished
            self.messaging.handle_events(
                self.position_to_modified_models,
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
        self, write_request: WriteRequest, migration_index: Optional[int] = None
    ) -> Tuple[int, Dict[Fqid, Dict[Field, JSON]]]:
        # Check locked_fields -> Possible LockedError
        self.occ_locker.assert_locked_fields(write_request)

        # Insert db events with position data
        if migration_index is None:
            migration_index = self.read_database.get_current_migration_index()
        position, modified_fqfields = self.database.insert_events(
            write_request.events,
            migration_index,
            write_request.information,
            write_request.user_id,
        )

        return position, modified_fqfields

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
