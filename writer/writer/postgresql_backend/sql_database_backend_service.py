from textwrap import dedent
from typing import Any, List, Set

from writer.core import (
    DbCreateEvent,
    DbDeleteEvent,
    DbDeleteFieldsEvent,
    DbRestoreEvent,
    DbUpdateEvent,
    InvalidFormat,
    ModelDoesNotExist,
    ModelExists,
    ModelNotDeleted,
    collectionfield_from_fqid_and_field,
)
from writer.di import service_as_singleton

from .connection_handler import ConnectionHandler
from .sql_event_types import EVENT_TYPES


# https://stackoverflow.com/questions/18404055/index-for-finding-an-element-in-a-json-array


FQID_MAX_LEN = 48
COLLECTION_MAX_LEN = 32
COLLECTIONFIELD_MAX_LEN = 255


@service_as_singleton
class SqlDatabaseBackendService:
    insert_event_statement = dedent(
        """\
        insert into events (position, fqid, type, data, fields)
        values (%s, %s, %s, %s, %s)"""
    )

    connection: ConnectionHandler

    def get_context(self):
        return self.connection.get_connection_context()

    def insert_events(self, events, information, user_id) -> int:
        if not events:
            raise RuntimeError()  # TODO

        position = self.create_position(information, user_id)
        for event in events:
            if len(event.fqid) > FQID_MAX_LEN:
                raise InvalidFormat(
                    f"fqid {event.fqid} is too long (max: {FQID_MAX_LEN})"
                )
            self.insert_event(event, position)
        self.update_modified_collectionfields(events, position)
        return position

    def create_position(self, information, user_id):
        statement = dedent(
            """\
            insert into positions (timestamp, user_id, information)
            values (current_timestamp, %s, %s)"""
        )
        arguments = [user_id, self.json(information)]
        self.connection.execute(statement, arguments)
        query = "select max(position) from positions"
        position = self.connection.query_single_value(query, [])
        return position

    def insert_event(self, event, position: int):
        if isinstance(event, DbCreateEvent):
            self.insert_create_event(event, position)
        if isinstance(event, DbUpdateEvent):
            self.insert_update_event(event, position)
        if isinstance(event, DbDeleteFieldsEvent):
            self.insert_delete_fields_event(event, position)
        if isinstance(event, DbDeleteEvent):
            self.insert_delete_event(event, position)
        if isinstance(event, DbRestoreEvent):
            self.insert_restore_event(event, position)

    def insert_create_event(self, create_event, position: int) -> None:
        if self.exists_query("models_lookup", "fqid=%s", [create_event.fqid]):
            raise ModelExists(create_event.fqid)

        arguments = [
            position,
            create_event.fqid,
            EVENT_TYPES.CREATE,
            self.json(create_event.field_data),
            self.json(create_event.get_fields()),
        ]
        self.connection.execute(self.insert_event_statement, arguments)
        statement = "insert into models_lookup (fqid, deleted) values (%s, %s)"
        arguments = [create_event.fqid, False]
        self.connection.execute(statement, arguments)

    def insert_update_event(self, update_event, position) -> None:
        self.assert_exists(update_event.fqid)

        arguments = [
            position,
            update_event.fqid,
            EVENT_TYPES.UPDATE,
            self.json(update_event.field_data),
            self.json(update_event.get_fields()),
        ]
        self.connection.execute(self.insert_event_statement, arguments)

    def insert_delete_fields_event(self, delete_fields_event, position: int) -> None:
        self.assert_exists(delete_fields_event.fqid)

        arguments = [
            position,
            delete_fields_event.fqid,
            EVENT_TYPES.DELETE_FIELDS,
            self.json(delete_fields_event.fields),
            self.json(delete_fields_event.fields),
        ]
        self.connection.execute(self.insert_event_statement, arguments)

    def insert_delete_event(self, delete_event, position: int) -> None:
        self.assert_exists(delete_event.fqid)

        model_fields = self.get_current_fields_from_model(delete_event.fqid)
        delete_event.set_modified_fields(model_fields)

        insert_arguments = [
            position,
            delete_event.fqid,
            EVENT_TYPES.DELETE,
            self.json(None),
            self.json(model_fields),
        ]
        self.connection.execute(self.insert_event_statement, insert_arguments)
        update_statement = "update models_lookup set deleted=%s where fqid=%s"
        update_arguments = [True, delete_event.fqid]
        self.connection.execute(update_statement, update_arguments)

    def assert_exists(self, fqid):
        if not self.exists_query(
            "models_lookup", "fqid=%s and deleted=%s", [fqid, False]
        ):
            raise ModelDoesNotExist(fqid)

    def exists_query(self, table, conditions, arguments):
        query = f"select exists(select 1 from {table} where {conditions})"
        result = self.connection.query_single_value(query, arguments)
        return result

    def get_current_fields_from_model(self, fqid):
        """ returns a list of fields for this model as it is in the read db """
        query = "select jsonb_object_keys(data) from models where fqid=%s"
        arguments = [fqid]
        return self.connection.query_list_of_single_values(query, arguments)

    def insert_restore_event(self, restore_event, position: int) -> None:
        if not self.exists_query(
            "models_lookup", "fqid=%s and deleted=%s", [restore_event.fqid, True]
        ):
            raise ModelNotDeleted(restore_event.fqid)

        model_fields = self.get_current_fields_from_deleted_model(restore_event.fqid)
        restore_event.set_modified_fields(model_fields)

        insert_arguments = [
            position,
            restore_event.fqid,
            EVENT_TYPES.RESTORE,
            self.json(None),
            self.json(model_fields),
        ]
        self.connection.execute(self.insert_event_statement, insert_arguments)
        update_statement = "update models_lookup set deleted=%s where fqid=%s"
        update_arguments = [False, restore_event.fqid]
        self.connection.execute(update_statement, update_arguments)

    def get_current_fields_from_deleted_model(self, fqid):
        # Note: Todo a restore, the last event must be a delete.
        # This means, we can get all model fields from the previous delete event.
        query = "select fields from events where fqid=%s order by id asc limit 1"
        arguments = [fqid]
        return self.connection.query_single_value(query, arguments)

    def update_modified_collectionfields(self, events, position: int) -> None:
        modified_collectionfields: Set[str] = set()
        for event in events:
            modified_collectionfields.update(self.get_modified_collectionfields(event))
        self.update_modified_collectionfields_in_database(
            modified_collectionfields, position
        )

    def get_modified_collectionfields(self, event):
        # use event.get_modified_fields() and event.fqid
        return [
            collectionfield_from_fqid_and_field(event.fqid, field)
            for field in event.get_modified_fields()
        ]

    def update_modified_collectionfields_in_database(
        self, collectionfields, position: int
    ) -> None:
        value_placeholders = []
        arguments: List[Any] = []
        for cf in collectionfields:
            if len(cf) > COLLECTIONFIELD_MAX_LEN:
                raise InvalidFormat(
                    f"Collection field {cf} is too long "
                    + "(max: {COLLECTIONFIELD_MAX_LEN})"
                )
            arguments.extend((cf, position,))
            value_placeholders.append("(%s, %s)")

        values = ",".join(value_placeholders)
        statement = dedent(
            f"""\
            insert into collectionfields (collectionfield, position) values {values}
            on conflict(collectionfield) do update set position=excluded.position;"""
        )
        self.connection.execute(statement, arguments)

    def json(self, data):
        return self.connection.to_json(data)

    def reserve_next_ids(self, collection: str, amount: int) -> List[int]:
        if amount <= 0:
            raise InvalidFormat(f"amount must be >= 1, not {amount}")
        if len(collection) > COLLECTION_MAX_LEN or not collection:
            raise InvalidFormat(
                f"collection length must be between 1 and {COLLECTION_MAX_LEN}"
            )

        query = "select id from id_sequences where collection=%s"
        arguments = [collection]
        low_id = self.connection.query_single_value(query, arguments)
        if low_id is None:
            low_id = 1
        high_id = low_id + amount  # high id not included in the result

        statement = "update id_sequences set id=%s where collection=%s"
        statement = dedent(
            f"""\
            insert into id_sequences (collection, id) values (%s, %s)
            on conflict(collection) do update set id=excluded.id;"""
        )
        arguments = [collection, high_id]
        self.connection.execute(statement, arguments)

        return list(range(low_id, high_id))
