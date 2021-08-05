from collections import defaultdict
from textwrap import dedent
from typing import Any, ContextManager, Dict, List, Tuple

from datastore.shared.di import service_as_singleton
from datastore.shared.postgresql_backend import (
    ALL_TABLES,
    EVENT_TYPES,
    ConnectionHandler,
)
from datastore.shared.services import ReadDatabase
from datastore.shared.typing import JSON, Field, Fqid, Id, Model, Position
from datastore.shared.util import (
    META_DELETED,
    META_POSITION,
    BadCodingError,
    DeletedModelsBehaviour,
    InvalidFormat,
    ModelDoesNotExist,
    ModelExists,
    ModelNotDeleted,
    collection_from_fqid,
    collectionfield_from_fqid_and_field,
    id_from_fqid,
    logger,
)
from datastore.writer.core import BaseRequestEvent

from .db_events import (
    BaseDbEvent,
    DbCreateEvent,
    DbDeleteEvent,
    DbDeleteFieldsEvent,
    DbListUpdateEvent,
    DbRestoreEvent,
    DbUpdateEvent,
)
from .event_translator import EventTranslator


# Max lengths of the important key parts:
# collection: 32
# id: 16
# field: 207
# -> collection + id + field = 255
COLLECTION_MAX_LEN = 32
FQID_MAX_LEN = 48  # collection + id
COLLECTIONFIELD_MAX_LEN = 239  # collection + field


# TODO: Make this a factory, so position and event_weight
# must not be passed through all calls.


@service_as_singleton
class SqlDatabaseBackendService:

    connection: ConnectionHandler
    read_database: ReadDatabase
    event_translator: EventTranslator

    def get_context(self) -> ContextManager[None]:
        return self.connection.get_connection_context()

    def insert_events(
        self,
        events: List[BaseRequestEvent],
        migration_index: int,
        information: JSON,
        user_id: int,
    ) -> Tuple[Position, Dict[Fqid, Dict[Field, JSON]]]:
        if not events:
            raise BadCodingError()

        position = self.create_position(migration_index, information, user_id)
        modified_models: Dict[Fqid, Dict[Field, JSON]] = defaultdict(dict)
        weight = 1
        for event in events:
            db_events = self.event_translator.translate(event)
            for db_event in db_events:
                if len(event.fqid) > FQID_MAX_LEN:
                    raise InvalidFormat(
                        f"fqid {db_event.fqid} is too long (max: {FQID_MAX_LEN})"
                    )
                self.insert_event(db_event, position, weight)
                modified_models[db_event.fqid].update(db_event.get_modified_fields())
                weight += 1
        return position, modified_models

    def create_position(
        self, migration_index: int, information: JSON, user_id: int
    ) -> Position:
        statement = dedent(
            """\
            insert into positions (timestamp, migration_index, user_id, information)
            values (current_timestamp, %s, %s, %s)"""
        )
        arguments = [migration_index, user_id, self.json(information)]
        self.connection.execute(statement, arguments)
        query = "select max(position) from positions"
        position = self.connection.query_single_value(query, [])
        logger.info(f"Created position {position}")
        return position

    def insert_event(
        self, event: BaseDbEvent, position: Position, event_weight: int
    ) -> None:
        if isinstance(event, DbCreateEvent):
            self.insert_create_event(event, position, event_weight)
        elif isinstance(event, DbUpdateEvent):
            self.insert_update_event(event, position, event_weight)
        elif isinstance(event, DbListUpdateEvent):
            self.insert_list_update_event(event, position, event_weight)
        elif isinstance(event, DbDeleteFieldsEvent):
            self.insert_delete_fields_event(event, position, event_weight)
        elif isinstance(event, DbDeleteEvent):
            self.insert_delete_event(event, position, event_weight)
        elif isinstance(event, DbRestoreEvent):
            self.insert_restore_event(event, position, event_weight)
        else:
            raise BadCodingError()

    def insert_db_event(
        self, event: BaseDbEvent, arguments: List[Any], position: Position
    ) -> None:
        """
        Adds a new event to the events table. Makes sure, that the `collectionfields`
        and `events_to_collectionfields` are updated.
        """
        event_id = self.connection.query_single_value(
            dedent(
                """\
                insert into events (position, fqid, type, data, weight)
                values (%s, %s, %s, %s, %s) returning id"""
            ),
            arguments,
        )
        self.attach_modified_fields_to_event(event_id, event, position)

    def create_model(self, fqid: Fqid, model: Model, position: Position) -> None:
        model[META_DELETED] = False
        self._set_model(fqid, model, position)

        statement = "insert into models_lookup (fqid, deleted) values (%s, %s)"
        self.connection.execute(statement, [fqid, False])

    def update_model(
        self,
        fqid: Fqid,
        field_values: Dict[Field, JSON],
        position: Position,
        get_deleted_models=DeletedModelsBehaviour.NO_DELETED,
    ) -> None:
        model = self.read_database.get(fqid, get_deleted_models=get_deleted_models)
        for field, value in field_values.items():
            if value is None:
                model.pop(field, None)
            else:
                model[field] = value
        self._set_model(fqid, model, position)

    def _set_model(self, fqid: str, model: Model, position: Position) -> None:
        model[META_POSITION] = position
        statement = """
            insert into models (fqid, data) values (%s, %s)
            on conflict(fqid) do update set data=excluded.data;"""
        self.connection.execute(statement, [fqid, self.json(model)])

    def delete_model(self, fqid: str, position: Position) -> None:
        self.update_model(fqid, {META_DELETED: True}, position)
        update_statement = "update models_lookup set deleted=%s where fqid=%s"
        self.connection.execute(update_statement, [True, fqid])

    def restore_model(self, fqid: str, position: Position) -> None:
        self.update_model(
            fqid,
            {META_DELETED: False},
            position,
            get_deleted_models=DeletedModelsBehaviour.ONLY_DELETED,
        )
        update_statement = "update models_lookup set deleted=%s where fqid=%s"
        self.connection.execute(update_statement, [False, fqid])

    def insert_create_event(
        self, create_event: DbCreateEvent, position: Position, event_weight: int
    ) -> None:
        if self.exists_query("models_lookup", "fqid=%s", [create_event.fqid]):
            raise ModelExists(create_event.fqid)

        # update max collection id if neccessary
        statement = dedent(
            """\
            insert into id_sequences (collection, id) values (%s, %s)
            on conflict(collection) do update
            set id=greatest(id_sequences.id, excluded.id);"""
        )
        arguments: List[Any] = [
            collection_from_fqid(create_event.fqid),
            int(id_from_fqid(create_event.fqid)) + 1,
        ]
        self.connection.execute(statement, arguments)

        arguments = [
            position,
            create_event.fqid,
            EVENT_TYPES.CREATE,
            self.json(create_event.field_data),
            event_weight,
        ]
        self.insert_db_event(create_event, arguments, position)

        self.create_model(create_event.fqid, create_event.field_data, position)

    def insert_update_event(
        self, update_event, position: Position, event_weight: int
    ) -> None:
        self.assert_exists(update_event.fqid)

        arguments = [
            position,
            update_event.fqid,
            EVENT_TYPES.UPDATE,
            self.json(update_event.field_data),
            event_weight,
        ]
        self.insert_db_event(update_event, arguments, position)

        self.update_model(
            update_event.fqid, update_event.get_modified_fields(), position
        )

    def insert_list_update_event(
        self,
        list_update_event: DbListUpdateEvent,
        position: Position,
        event_weight: int,
    ) -> None:
        self.assert_exists(list_update_event.fqid)

        data = {"add": list_update_event.add, "remove": list_update_event.remove}
        arguments = [
            position,
            list_update_event.fqid,
            EVENT_TYPES.LIST_FIELDS,
            self.json(data),
            event_weight,
        ]
        self.insert_db_event(list_update_event, arguments, position)

        self.update_model(
            list_update_event.fqid, list_update_event.get_modified_fields(), position
        )

    def insert_delete_fields_event(
        self, delete_fields_event, position: Position, event_weight: int
    ) -> None:
        self.assert_exists(delete_fields_event.fqid)

        arguments = [
            position,
            delete_fields_event.fqid,
            EVENT_TYPES.DELETE_FIELDS,
            self.json(delete_fields_event.fields),
            event_weight,
        ]
        self.insert_db_event(delete_fields_event, arguments, position)

        self.update_model(
            delete_fields_event.fqid,
            delete_fields_event.get_modified_fields(),
            position,
        )

    def insert_delete_event(
        self, delete_event, position: Position, event_weight: int
    ) -> None:
        self.assert_exists(delete_event.fqid)

        arguments = [
            position,
            delete_event.fqid,
            EVENT_TYPES.DELETE,
            self.json(None),
            event_weight,
        ]
        self.insert_db_event(delete_event, arguments, position)

        self.delete_model(delete_event.fqid, position)

    def insert_restore_event(
        self, restore_event, position: Position, event_weight: int
    ) -> None:
        if not self.exists_query(
            "models_lookup", "fqid=%s and deleted=%s", [restore_event.fqid, True]
        ):
            raise ModelNotDeleted(restore_event.fqid)

        arguments = [
            position,
            restore_event.fqid,
            EVENT_TYPES.RESTORE,
            self.json(None),
            event_weight,
        ]
        self.insert_db_event(restore_event, arguments, position)

        self.restore_model(restore_event.fqid, position)

    def assert_exists(self, fqid):
        if not self.exists_query(
            "models_lookup", "fqid=%s and deleted=%s", [fqid, False]
        ):
            raise ModelDoesNotExist(fqid)

    def exists_query(self, table, conditions, arguments):
        query = f"select exists(select 1 from {table} where {conditions})"
        result = self.connection.query_single_value(query, arguments)
        return result

    def attach_modified_fields_to_event(self, event_id, event, position):
        modified_collectionfields = self.get_modified_collectionfields_from_event(event)
        if not modified_collectionfields:
            return

        collectionfield_ids = self.insert_modified_collectionfields_into_db(
            modified_collectionfields, position
        )
        self.connect_events_and_collection_fields(event_id, collectionfield_ids)

    def get_modified_collectionfields_from_event(self, event):
        return [
            collectionfield_from_fqid_and_field(event.fqid, field)
            for field in event.get_modified_fields()
        ]

    def insert_modified_collectionfields_into_db(
        self, modified_collectionfields, position
    ):
        # insert into db, updating all existing fields with position, returning ids
        value_placeholders = []
        arguments: List[Any] = []
        for collectionfield in modified_collectionfields:
            if len(collectionfield) > COLLECTIONFIELD_MAX_LEN:
                raise InvalidFormat(
                    f"Collection field {collectionfield} is too long "
                    + "(max: {COLLECTIONFIELD_MAX_LEN})"
                )
            arguments.extend(
                (
                    collectionfield,
                    position,
                )
            )
            value_placeholders.append("(%s, %s)")

        values = ",".join(value_placeholders)
        statement = dedent(
            f"""\
            insert into collectionfields (collectionfield, position) values {values}
            on conflict(collectionfield) do update set position=excluded.position
            returning id"""
        )
        return self.connection.query_list_of_single_values(statement, arguments)

    def connect_events_and_collection_fields(self, event_id, collectionfield_ids):
        # create m2m relations
        value_placeholders = []
        arguments: List[Any] = []
        for collectionfield_id in collectionfield_ids:
            arguments.extend(
                (
                    event_id,
                    collectionfield_id,
                )
            )
            value_placeholders.append("(%s, %s)")

        values = ",".join(value_placeholders)
        statement = f"insert into events_to_collectionfields (event_id, collectionfield_id) values {values}"
        self.connection.execute(statement, arguments)

    def json(self, data):
        return self.connection.to_json(data)

    def reserve_next_ids(self, collection: str, amount: int) -> List[Id]:
        if amount <= 0:
            raise InvalidFormat(f"amount must be >= 1, not {amount}")
        if len(collection) > COLLECTION_MAX_LEN or not collection:
            raise InvalidFormat(
                f"collection length must be between 1 and {COLLECTION_MAX_LEN}"
            )

        statement = dedent(
            """\
            insert into id_sequences (collection, id) values (%s, %s)
            on conflict(collection) do update
            set id=id_sequences.id + excluded.id - 1 returning id;"""
        )
        arguments = [collection, amount + 1]
        new_max_id = self.connection.query_single_value(statement, arguments)

        return list(range(new_max_id - amount, new_max_id))

    def truncate_db(self) -> None:
        for table in ALL_TABLES:
            self.connection.execute(f"DELETE FROM {table} CASCADE;", [])
        # restart sequences manually to provide a clean db
        for seq in ("positions_position", "events_id", "collectionfields_id"):
            self.connection.execute(f"ALTER SEQUENCE {seq}_seq RESTART WITH 1;", [])
