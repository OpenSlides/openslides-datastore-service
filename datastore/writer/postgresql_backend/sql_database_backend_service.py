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


class MultiInsert:
    check_models_exist: List[str]
    insert_events: List[List[Any]]
    insert_id_sequences: Dict[str, int]
    insert_models: Dict[str, Tuple[Any, Any]]

    def __init__(self) -> None:
        self.check_models_exist = []
        self.insert_events = []
        self.insert_id_sequences = {}
        self.insert_models = {}


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
        multi_insert = MultiInsert()
        all_db_events = []  # TODO: remove me
        for event in events:
            db_events = self.event_translator.translate(
                event, multi_insert.insert_models
            )
            for db_event in db_events:
                if len(event.fqid) > FQID_MAX_LEN:
                    raise InvalidFormat(
                        f"fqid {db_event.fqid} is too long (max: {FQID_MAX_LEN})"
                    )
                self.insert_event(db_event, position, weight, multi_insert)
                modified_models[db_event.fqid].update(db_event.get_modified_fields())
                weight += 1

                all_db_events.append(db_event)  # TODO: remove me

        if len(multi_insert.check_models_exist) > 0:
            if self.exists_query(
                "models", "fqid in %s", (tuple(multi_insert.check_models_exist),)
            ):
                raise ModelExists("eines von vielen")

        if len(multi_insert.insert_id_sequences) > 0:
            insert_id_sequences: List[Tuple[str, int]] = []
            for collection, id in multi_insert.insert_id_sequences.items():
                insert_id_sequences.append((collection, id))

            # update max collection id if neccessary
            self.connection.execute_values(
                dedent(
                    """\
                    insert into id_sequences (collection, id) values %s
                    on conflict(collection) do update
                    set id=greatest(id_sequences.id, excluded.id) RETURNING 1;"""
                ),
                insert_id_sequences,
            )

        insert_model_sequence: List[Tuple[Any, Any, Any]] = []
        for fqfield, data in multi_insert.insert_models.items():
            insert_model_sequence.append((fqfield, self.json(data[0]), data[1]))

        self.connection.execute_values(
            "insert into models (fqid, data, deleted) values %s on conflict(fqid) do update set data=excluded.data, deleted=excluded.deleted RETURNING 1;",
            insert_model_sequence,
        )

        result = self.connection.execute_values(
            "INSERT INTO events (position, fqid, type, data, weight) VALUES %s RETURNING id",
            multi_insert.insert_events,
        )
        ids = list(map(lambda row: row[0], result))

        # TODO: Remove loop
        for index, db_event in enumerate(all_db_events):
            self.attach_modified_fields_to_event(ids[index], db_event, position)

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
        self,
        event: BaseDbEvent,
        position: Position,
        event_weight: int,
        multi_insert: MultiInsert,
    ) -> None:
        if isinstance(event, DbCreateEvent):
            self.insert_create_event(event, position, event_weight, multi_insert)
        elif isinstance(event, DbUpdateEvent):
            self.insert_update_event(event, position, event_weight, multi_insert)
        elif isinstance(event, DbListUpdateEvent):
            self.insert_list_update_event(event, position, event_weight, multi_insert)
        elif isinstance(event, DbDeleteFieldsEvent):
            self.insert_delete_fields_event(event, position, event_weight, multi_insert)
        elif isinstance(event, DbDeleteEvent):
            self.insert_delete_event(event, position, event_weight, multi_insert)
        elif isinstance(event, DbRestoreEvent):
            self.insert_restore_event(event, position, event_weight, multi_insert)
        else:
            raise BadCodingError()

    def insert_db_event(
        self, event: BaseDbEvent, arguments: List[Any], position: Position
    ) -> List[Any]:
        """
        Adds a new event to the events table. Makes sure, that the `collectionfields`
        and `events_to_collectionfields` are updated.
        """
        return arguments

    def create_model(
        self, fqid: Fqid, model: Model, position: Position, multi_insert: MultiInsert
    ) -> None:
        model[META_DELETED] = False
        self._set_model(fqid, model, position, multi_insert)

    def update_model(
        self,
        fqid: Fqid,
        field_values: Dict[Field, JSON],
        position: Position,
        multi_insert: MultiInsert,
        get_deleted_models=DeletedModelsBehaviour.NO_DELETED,
    ) -> None:
        model = multi_insert.insert_models.get(fqid)
        if model is None:
            model = self.read_database.get(fqid, get_deleted_models=get_deleted_models)
        else:
            model = model[0]

        for field, value in field_values.items():
            if value is None:
                model.pop(field, None)
            else:
                model[field] = value
        self._set_model(fqid, model, position, multi_insert)

    def delete_model(
        self, fqid: str, position: Position, multi_insert: MultiInsert
    ) -> None:
        self.update_model(fqid, {META_DELETED: True}, position, multi_insert)

    def restore_model(
        self, fqid: str, position: Position, multi_insert: MultiInsert
    ) -> None:
        self.update_model(
            fqid,
            {META_DELETED: False},
            position,
            multi_insert,
            get_deleted_models=DeletedModelsBehaviour.ONLY_DELETED,
        )

    def _set_model(
        self, fqid: str, model: Model, position: Position, multi_insert: MultiInsert
    ) -> None:
        """META_DELETED must be in `model`"""
        model[META_POSITION] = position
        multi_insert.insert_models[fqid] = (model, model[META_DELETED])

    def insert_create_event(
        self,
        create_event: DbCreateEvent,
        position: Position,
        event_weight: int,
        multi_insert: MultiInsert,
    ) -> None:
        multi_insert.check_models_exist.append(create_event.fqid)
        multi_insert.insert_id_sequences[collection_from_fqid(create_event.fqid)] = (
            int(id_from_fqid(create_event.fqid)) + 1
        )

        arguments = [
            position,
            create_event.fqid,
            EVENT_TYPES.CREATE,
            self.json(create_event.field_data),
            event_weight,
        ]
        insert_event = self.insert_db_event(create_event, arguments, position)
        multi_insert.insert_events.append(insert_event)

        self.create_model(
            create_event.fqid, create_event.field_data, position, multi_insert
        )

    def insert_update_event(
        self,
        update_event,
        position: Position,
        event_weight: int,
        multi_insert: MultiInsert,
    ) -> None:
        self.assert_exists(update_event.fqid)

        arguments = [
            position,
            update_event.fqid,
            EVENT_TYPES.UPDATE,
            self.json(update_event.field_data),
            event_weight,
        ]
        insert_event = self.insert_db_event(update_event, arguments, position)
        multi_insert.insert_events.append(insert_event)

        self.update_model(
            update_event.fqid,
            update_event.get_modified_fields(),
            position,
            multi_insert,
        )

    def insert_list_update_event(
        self,
        list_update_event: DbListUpdateEvent,
        position: Position,
        event_weight: int,
        multi_insert: MultiInsert,
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
        insert_event = self.insert_db_event(list_update_event, arguments, position)
        multi_insert.insert_events.append(insert_event)

        self.update_model(
            list_update_event.fqid,
            list_update_event.get_modified_fields(),
            position,
            multi_insert,
        )

    def insert_delete_fields_event(
        self,
        delete_fields_event,
        position: Position,
        event_weight: int,
        multi_insert: MultiInsert,
    ) -> None:
        self.assert_exists(delete_fields_event.fqid)

        arguments = [
            position,
            delete_fields_event.fqid,
            EVENT_TYPES.DELETE_FIELDS,
            self.json(delete_fields_event.fields),
            event_weight,
        ]
        insert_event = self.insert_db_event(delete_fields_event, arguments, position)
        multi_insert.insert_events.append(insert_event)

        self.update_model(
            delete_fields_event.fqid,
            delete_fields_event.get_modified_fields(),
            position,
            multi_insert,
        )

    def insert_delete_event(
        self,
        delete_event,
        position: Position,
        event_weight: int,
        multi_insert: MultiInsert,
    ) -> None:
        self.assert_exists(delete_event.fqid)

        arguments = [
            position,
            delete_event.fqid,
            EVENT_TYPES.DELETE,
            self.json(None),
            event_weight,
        ]
        insert_event = self.insert_db_event(delete_event, arguments, position)
        multi_insert.insert_events.append(insert_event)

        self.delete_model(delete_event.fqid, position, multi_insert)

    def insert_restore_event(
        self,
        restore_event,
        position: Position,
        event_weight: int,
        multi_insert: MultiInsert,
    ) -> None:
        if not self.exists_query(
            "models", "fqid=%s and deleted=%s", [restore_event.fqid, True]
        ):
            raise ModelNotDeleted(restore_event.fqid)

        arguments = [
            position,
            restore_event.fqid,
            EVENT_TYPES.RESTORE,
            self.json(None),
            event_weight,
        ]
        insert_event = self.insert_db_event(restore_event, arguments, position)
        multi_insert.insert_events.append(insert_event)

        self.restore_model(restore_event.fqid, position)

    def assert_exists(self, fqid):
        # TODO: Also check if exist in multi_insert
        # if not self.exists_query("models", "fqid=%s and deleted=%s", [fqid, False]):
        #     raise ModelDoesNotExist(fqid)
        pass

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
        # TODO: Fix SQL Injection
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
