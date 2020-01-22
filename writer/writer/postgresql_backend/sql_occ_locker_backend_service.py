from typing import List

from writer.core import ModelLocked, fqid_and_field_from_fqfield
from writer.di import service_as_factory

from .connection_handler import ConnectionHandler


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

        query_arguments: List[str] = []
        filter_parts = []
        for fqfield, position in fqfields.items():
            fqid, field = fqid_and_field_from_fqfield(fqfield)
            field = self.connection.to_json(field)
            query_arguments.extend((fqid, field, position,))
            filter_parts.append("""(fqid=%s and fields @> %s::jsonb and position>%s)""")
        query = (
            "select fqid from events where " + " or ".join(filter_parts) + " limit 1"
        )

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
