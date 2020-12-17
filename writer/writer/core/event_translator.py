from typing import Dict, List, Protocol

from shared.di import service_as_singleton, service_interface
from shared.services import ReadDatabase
from shared.typing import JSON
from shared.util import BadCodingError, DeletedModelsBehaviour, InvalidFormat
from writer.core.db_events import (
    BaseDbEvent,
    DbCreateEvent,
    DbDeleteEvent,
    DbDeleteFieldsEvent,
    DbRestoreEvent,
    DbUpdateEvent,
)

from .write_request import (
    BaseRequestEvent,
    RequestCreateEvent,
    RequestDeleteEvent,
    RequestRestoreEvent,
    RequestUpdateEvent,
)


@service_interface
class EventTranslator(Protocol):
    def translate(self, request_events: List[BaseRequestEvent]) -> List[BaseDbEvent]:
        """
        Translates request events into db events
        """


@service_as_singleton
class EventTranslatorService:
    read_database: ReadDatabase

    def translate(self, request_events: List[BaseRequestEvent]) -> List[BaseDbEvent]:
        translated_events: List[BaseDbEvent] = []
        for event in request_events:
            translated_events += self.translate_single(event)
        return translated_events

    def translate_single(self, request_event: BaseRequestEvent) -> List[BaseDbEvent]:
        if isinstance(request_event, RequestCreateEvent):
            return [DbCreateEvent(request_event.fqid, request_event.fields)]
        if isinstance(request_event, RequestUpdateEvent):
            return self.create_update_events(request_event)
        if isinstance(request_event, RequestDeleteEvent):
            return [DbDeleteEvent(request_event.fqid)]
        if isinstance(request_event, RequestRestoreEvent):
            return [DbRestoreEvent(request_event.fqid)]
        raise BadCodingError()

    def create_update_events(
        self, request_update_event: RequestUpdateEvent
    ) -> List[BaseDbEvent]:
        db_events: List[BaseDbEvent] = []
        updated_fields: Dict[str, JSON] = {
            field: value
            for field, value in request_update_event.fields.items()
            if value is not None
        }
        if updated_fields:
            db_events.append(DbUpdateEvent(request_update_event.fqid, updated_fields))

        deleted_fields = [
            field
            for field, value in request_update_event.fields.items()
            if value is None
        ]
        if deleted_fields:
            db_events.append(
                DbDeleteFieldsEvent(request_update_event.fqid, deleted_fields)
            )

        list_field_updates = self.parse_list_field_updates(request_update_event)
        if list_field_updates:
            db_events.append(
                DbUpdateEvent(request_update_event.fqid, list_field_updates)
            )

        return db_events

    def parse_list_field_updates(self, event: RequestUpdateEvent) -> Dict[str, JSON]:
        add_fields = event.list_fields.get("add", {})
        remove_fields = event.list_fields.get("remove", {})
        all_field_keys = list(add_fields.keys()) + list(remove_fields.keys())
        if not all_field_keys:
            return {}

        model = self.read_database.get(
            event.fqid, all_field_keys, DeletedModelsBehaviour.ALL_MODELS
        )

        update_fields = {}
        for field in all_field_keys:
            db_list = model.get(field, [])
            if not isinstance(db_list, list):
                raise InvalidFormat(
                    f"Field {field} on model {event.fqid} is not a list, but of type"
                    + str(type(db_list))
                )
            for el in db_list:
                if not isinstance(el, (str, int)):
                    raise InvalidFormat(
                        f"Field {field} on model {event.fqid} contains invalid entry "
                        f"for list update (of type {type(el)}): {el}"
                    )

        for field, value in add_fields.items():
            # Iterate over list and remove all entries from value which are already
            # in the list. If adding multiple entries, this reduces the runtime needed.
            # When a huge amount of data is added, the normal update should be used
            # instead.
            db_list = model.get(field, [])
            for el in db_list:
                if el in value:
                    value.remove(el)
            update_fields[field] = db_list + value

        for field, value in remove_fields.items():
            if field in model:
                db_list = model.get(field)
                updated_list = [el for el in db_list if el not in value]
                if len(db_list) == len(updated_list):
                    # do not create update events for noops
                    continue
                update_fields[field] = updated_list

        return update_fields
