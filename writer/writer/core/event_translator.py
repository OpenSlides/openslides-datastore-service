from typing import Dict, List, Protocol

from writer.di import service_as_singleton, service_interface
from writer.shared.typing import JSON

from .db_events import (
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
        raise RuntimeError()

    def create_update_events(
        self, request_update_event: RequestUpdateEvent
    ) -> List[BaseDbEvent]:
        updated_fields: Dict[str, JSON] = {
            field: value
            for field, value in request_update_event.fields.items()
            if value is not None
        }
        deleted_fields = [
            field
            for field, value in request_update_event.fields.items()
            if value is None
        ]

        db_events: List[BaseDbEvent] = []
        if updated_fields:
            db_events.append(DbUpdateEvent(request_update_event.fqid, updated_fields))
        if deleted_fields:
            db_events.append(
                DbDeleteFieldsEvent(request_update_event.fqid, deleted_fields)
            )
        return db_events
