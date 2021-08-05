from typing import Dict, List, Protocol

from datastore.shared.di import service_as_singleton, service_interface
from datastore.shared.services import ReadDatabase
from datastore.shared.typing import JSON
from datastore.shared.util import BadCodingError, DeletedModelsBehaviour
from datastore.writer.core import (
    BaseRequestEvent,
    RequestCreateEvent,
    RequestDeleteEvent,
    RequestRestoreEvent,
    RequestUpdateEvent,
)

from .db_events import (
    BaseDbEvent,
    DbCreateEvent,
    DbDeleteEvent,
    DbDeleteFieldsEvent,
    DbListUpdateEvent,
    DbRestoreEvent,
    DbUpdateEvent,
)


@service_interface
class EventTranslator(Protocol):
    def translate(self, request_event: BaseRequestEvent) -> List[BaseDbEvent]:
        """
        Translates request events into db events
        """


@service_as_singleton
class EventTranslatorService:

    read_database: ReadDatabase

    def translate(self, request_event: BaseRequestEvent) -> List[BaseDbEvent]:
        if isinstance(request_event, RequestCreateEvent):
            return [DbCreateEvent(request_event.fqid, request_event.fields)]

        if isinstance(request_event, RequestUpdateEvent):
            return self.create_update_events(request_event)

        if isinstance(request_event, RequestDeleteEvent):
            model_fields = list(self.read_database.get(request_event.fqid).keys())
            return [DbDeleteEvent(request_event.fqid, model_fields)]

        if isinstance(request_event, RequestRestoreEvent):
            model_fields = list(
                self.read_database.get(
                    request_event.fqid,
                    get_deleted_models=DeletedModelsBehaviour.ONLY_DELETED,
                ).keys()
            )
            return [DbRestoreEvent(request_event.fqid, model_fields)]

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

        add = request_update_event.list_fields.get("add", {})
        remove = request_update_event.list_fields.get("remove", {})
        if add or remove:
            model = self.read_database.get(request_update_event.fqid)
            db_events.append(
                DbListUpdateEvent(request_update_event.fqid, add, remove, model)
            )

        return db_events
