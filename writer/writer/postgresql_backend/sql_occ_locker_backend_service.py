from textwrap import dedent
from typing import Any, Dict, List

from shared.di import service_as_factory
from shared.postgresql_backend import ConnectionHandler
from shared.postgresql_backend.sql_query_helper import SqlQueryHelper
from shared.services import ReadDatabase
from shared.util import ModelLocked, collectionfield_and_fqid_from_fqfield
from writer.core import CollectionFieldLock


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

    def assert_fqid_positions(self, fqids: Dict[str, int]) -> None:
        if not fqids:
            return

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
        query = (
            "select fqid from events where " + " or ".join(filter_parts) + " limit 1"
        )

        self.raise_model_locked_if_match(query, query_arguments)

    def assert_fqfield_positions(self, fqfields: Dict[str, int]) -> None:
        if not fqfields:
            return

        event_query_arguments: List[Any] = []
        event_filter_parts = []
        collectionfield_query_arguments: List[str] = []
        collectionfield_filter_parts = []

        for fqfield, position in fqfields.items():
            collectionfield, fqid = collectionfield_and_fqid_from_fqfield(fqfield)

            event_query_arguments.extend(
                (
                    fqid,
                    position,
                )
            )
            event_filter_parts.append("(fqid=%s and position>%s)")

            # % matches zero or more chars: this is correct since the template field
            # itself may also be locked
            # only replace template fields, not structured fields
            collectionfield = collectionfield.replace("$_", "$%_")
            if collectionfield.endswith("$"):
                # also add % if the placeholder is at the end of the collectionfield
                collectionfield += "%"
            # _ is the postgres wild card for a single character so we have to escape
            # all underscores
            collectionfield = collectionfield.replace("_", r"\_")

            collectionfield_query_arguments.extend(
                (
                    fqid,
                    collectionfield,
                )
            )
            collectionfield_filter_parts.append(
                "(e.fqid=%s and cf.collectionfield LIKE %s)"
            )

        event_filter = " or ".join(event_filter_parts)
        collectionfield_filter = " or ".join(collectionfield_filter_parts)
        query = dedent(
            f"""\
            select e.fqid from (
                select id, fqid from events where {event_filter}
            ) e
            inner join events_to_collectionfields ecf on e.id=ecf.event_id
            inner join collectionfields cf on ecf.collectionfield_id=cf.id
            where {collectionfield_filter} limit 1"""
        )
        query_arguments = event_query_arguments + collectionfield_query_arguments

        self.raise_model_locked_if_match(query, query_arguments)

    def assert_collectionfield_positions(
        self, collectionfields: Dict[str, CollectionFieldLock]
    ) -> None:
        if not collectionfields:
            return

        query_arguments: List[Any] = []
        filter_parts = []
        for collectionfield, cf_lock in collectionfields.items():
            if isinstance(cf_lock, int):
                query_arguments.extend(
                    (
                        collectionfield,
                        cf_lock,
                    )
                )
                filter_parts.append("(cf.collectionfield=%s and e.position>%s)")
            else:
                for lock in cf_lock:
                    query_arguments.extend(
                        (
                            lock.position,
                            collectionfield,
                        )
                    )
                    filter_part = "(e.position>%s and cf.collectionfield=%s"
                    if lock.filter:
                        filter_part += " and " + self.query_helper.build_filter_str(
                            lock.filter, query_arguments, "m"
                        )
                    filter_part += ")"
                    filter_parts.append(filter_part)

        filter_query = " or ".join(filter_parts)
        query = dedent(
            f"""\
            select collectionfield from collectionfields cf
            inner join events_to_collectionfields ecf on cf.id=ecf.collectionfield_id
            inner join events e on ecf.event_id=e.id
            inner join models m on e.fqid=m.fqid
            where {filter_query} limit 1"""
        )
        self.raise_model_locked_if_match(query, query_arguments)

    def raise_model_locked_if_match(self, query, arguments):
        """ returns str (the only response) or None if there is no row """
        locked_key = self.connection.query_single_value(query, arguments)
        if locked_key is not None:
            raise ModelLocked(locked_key)
