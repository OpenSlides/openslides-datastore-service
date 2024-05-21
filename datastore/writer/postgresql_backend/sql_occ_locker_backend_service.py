from collections import defaultdict
from textwrap import dedent
from typing import Any, Dict, List, Sequence, Set, Tuple

from datastore.shared.di import service_as_factory
from datastore.shared.postgresql_backend import ConnectionHandler
from datastore.shared.postgresql_backend.sql_query_helper import SqlQueryHelper
from datastore.shared.services import ReadDatabase
from datastore.shared.util import (
    KEYSEPARATOR,
    ModelLocked,
    collectionfield_and_fqid_from_fqfield,
)
from datastore.writer.core import CollectionFieldLock, WriteRequest


# FQID LOCKING
# positions:    <1> <2> <3> <4> <5>
# a/1 modified:  X           X
# Lock a/1 with pos 4, 5: OK
# Lock a/1 with pos 3, 2, ..: not OK
# Lock a/1 with pos P: Exists an event with pos>P -> not OK


@service_as_factory
class SqlOccLockerBackendService:
    connection: ConnectionHandler
    read_db: ReadDatabase
    query_helper: SqlQueryHelper

    def assert_locked_fields(self, write_request: WriteRequest) -> None:
        """May raise a ModelLockedException"""
        broken_locks = set()
        broken_locks.update(self.get_locked_fqids(write_request.locked_fqids))
        broken_locks.update(self.get_locked_fqfields(write_request.locked_fqfields))
        broken_locks.update(
            self.get_locked_collectionfields(write_request.locked_collectionfields)
        )
        if broken_locks:
            raise ModelLocked(list(broken_locks))

    def get_locked_fqids(self, fqids: Dict[str, int]) -> List[str]:
        if not fqids:
            return []

        query_arguments: List[Any] = []
        filter_parts = []
        for fqid, position in fqids.items():
            query_arguments.extend(
                (
                    fqid,
                    position,
                )
            )
            filter_parts.append("(fqid=%s and position>%s)")
        query = "select fqid from events where " + " or ".join(filter_parts)

        return self.connection.query_list_of_single_values(query, query_arguments)

    def get_locked_fqfields(self, fqfields: Dict[str, int]) -> List[str]:
        if not fqfields:
            return []

        event_query_arguments: List[Any] = []
        event_filter_parts = []
        collectionfield_query_arguments: List[Sequence[str]] = []
        fqid_position_set: Set[Tuple[str, int]] = set()
        collectionfield_query_data: Dict[str, List[str]] = defaultdict(list)

        for fqfield, position in fqfields.items():
            collectionfield, fqid = collectionfield_and_fqid_from_fqfield(fqfield)

            if (fqid, position) not in fqid_position_set:
                fqid_position_set.add((fqid, position))
                event_query_arguments.extend(
                    (
                        fqid,
                        position,
                    )
                )
                event_filter_parts.append("(e.fqid=%s and e.position>%s)")

            collectionfield_query_data[fqid].append(collectionfield)

        event_filter = " or ".join(event_filter_parts)
        collectionfield_filter = " or ".join(
            ["(fqid=%s and collectionfield = ANY(%s))"]
            * len(collectionfield_query_data)
        )
        collectionfield_query_arguments = [
            argument for item in collectionfield_query_data.items() for argument in item
        ]
        query = dedent(
            f"""\
            select e.fqid || %s || split_part(cf.collectionfield, %s, 2) from events e
                inner join events_to_collectionfields ecf on e.id=ecf.event_id
                inner join collectionfields cf on ecf.collectionfield_id=cf.id
            where ({event_filter}) and ({collectionfield_filter})"""
        )
        query_arguments = (
            [KEYSEPARATOR] * 2 + event_query_arguments + collectionfield_query_arguments
        )
        return self.connection.query_list_of_single_values(query, query_arguments)

    def get_locked_collectionfields(
        self, collectionfields: Dict[str, CollectionFieldLock]
    ) -> List[str]:
        if not collectionfields:
            return []

        query_arguments: List[Any] = []
        filter_parts = []
        joins_needed = False
        for collectionfield, cf_lock in collectionfields.items():
            if isinstance(cf_lock, int):
                query_arguments.extend(
                    (
                        collectionfield,
                        cf_lock,
                    )
                )
                filter_parts.append("(cf.collectionfield=%s and cf.position>%s)")
            else:
                joins_needed = True
                for lock in cf_lock:
                    query_arguments.extend(
                        (
                            lock.position,
                            collectionfield,
                        )
                    )
                    filter_part = "(e.position>%s and cf.collectionfield=%s"
                    if lock.filter:
                        filter_part += (
                            " and ("
                            + self.query_helper.build_filter_str(
                                lock.filter, query_arguments, "m"
                            )
                            + ")"
                        )
                    filter_part += ")"
                    filter_parts.append(filter_part)

        filter_query = " or ".join(filter_parts)
        joins = """\
            inner join events_to_collectionfields ecf on cf.id=ecf.collectionfield_id
            inner join events e on ecf.event_id=e.id
            inner join models m on e.fqid=m.fqid
        """
        query = dedent(
            f"""\
            select collectionfield from collectionfields cf
            {joins if joins_needed else ""}
            where {filter_query}"""
        )
        return self.connection.query_list_of_single_values(query, query_arguments)
