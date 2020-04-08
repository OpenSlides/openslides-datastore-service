from textwrap import dedent
from typing import List

from shared.core import ModelLocked, collectionfield_and_fqid_from_fqfield
from shared.di import service_as_factory
from shared.postgresql_backend import ConnectionHandler


# FQID LOCKING
# positions:    <1> <2> <3> <4> <5>
# a/1 modified:  X           X
# Lock a/1 with pos 4, 5: OK
# Lock a/1 with pos 3, 2, ..: not OK
# Lock a/1 with pos P: Exists an event with pos>P -> not OK


@service_as_factory
class SqlOccLockerBackendService:
    connection: ConnectionHandler

    def assert_fqid_positions(self, fqids):
        if not fqids:
            return

        query_arguments: List[str] = []
        filter_parts = []
        for fqid, position in fqids.items():
            query_arguments.extend((fqid, position,))
            filter_parts.append("(fqid=%s and position>%s)")
        query = (
            "select fqid from events where " + " or ".join(filter_parts) + " limit 1"
        )

        self.raise_model_locked_if_match(query, query_arguments)

    def assert_fqfield_positions(self, fqfields):
        if not fqfields:
            return

        event_query_arguments: List[str] = []
        event_filter_parts = []
        collectionfield_query_arguments: List[str] = []
        collectionfield_filter_parts = []

        for fqfield, position in fqfields.items():
            collectionfield, fqid = collectionfield_and_fqid_from_fqfield(fqfield)

            event_query_arguments.extend((fqid, position,))
            event_filter_parts.append("(fqid=%s and position>%s)")

            collectionfield = collectionfield.replace("_", r"\_")
            collectionfield = collectionfield.replace("$", "_%")

            collectionfield_query_arguments.extend((fqid, collectionfield,))
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

    def assert_collectionfield_positions(self, collectionfields):
        if not collectionfields:
            return

        query_arguments: List[str] = []
        filter_parts = []
        for collectionfield, position in collectionfields.items():
            query_arguments.extend((collectionfield, position,))
            filter_parts.append("(collectionfield=%s and position>%s)")
        query = (
            "select collectionfield from collectionfields where "
            + " or ".join(filter_parts)
            + " limit 1"
        )

        self.raise_model_locked_if_match(query, query_arguments)

    def raise_model_locked_if_match(self, query, arguments):
        """ returns str (the only response) or None if there is no row """
        locked_key = self.connection.query_single_value(query, arguments)
        if locked_key is not None:
            raise ModelLocked(locked_key)
