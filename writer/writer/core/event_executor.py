import copy
from typing import Dict, List, Protocol

from shared.di import service_as_factory, service_interface
from shared.services import ReadDatabase
from shared.util import (
    META_DELETED,
    META_POSITION,
    BadCodingError,
    DeletedModelsBehaviour,
)
from writer.core.db_events import (
    BaseDbEvent,
    DbCreateEvent,
    DbDeleteEvent,
    DbDeleteFieldsEvent,
    DbListUpdateEvent,
    DbRestoreEvent,
    DbUpdateEvent,
)


@service_interface
class EventExecutor(Protocol):
    def update(self, events: List[BaseDbEvent], position: int) -> None:
        """Execute the given list of events."""


class MODEL_STATUS:
    WRITE, DELETE, RESTORE = range(3)


@service_as_factory
class EventExecutorService:

    read_database: ReadDatabase

    def update(self, events: List[BaseDbEvent], position: int) -> None:
        self.events = events
        self.position = position

        self.models = self.get_models()
        self.model_status: Dict[str, int] = {}  # maps fqid<->MODEL_STATUS

        self.execute_events()
        self.restore_models()
        self.add_position()
        self.write_back()

    def get_models(self):
        modified_fqids = list(set(event.fqid for event in self.events))
        return self.read_database.get_many(
            modified_fqids, {}, DeletedModelsBehaviour.ALL_MODELS
        )

    def execute_events(self) -> None:
        for event in self.events:
            if self.model_status.get(event.fqid) in (
                MODEL_STATUS.RESTORE,
                MODEL_STATUS.DELETE,
            ):
                if isinstance(event, (DbDeleteEvent, DbRestoreEvent)):
                    self.execute_event(event)
                continue
                # Skip creates and updates for this element. This
                # element will either be restored in the write-back phase or
                # deleted. If it is restored, the correct data will be builded
                # from all correct and up-to-date events in the database.

            self.execute_event(event)

    def execute_event(self, event) -> None:
        if isinstance(event, DbCreateEvent):
            self.models[event.fqid] = copy.deepcopy(
                event.field_data
            )  # TODO test this and explain why it is important
            self.model_status[event.fqid] = MODEL_STATUS.WRITE

        elif isinstance(event, DbRestoreEvent):
            if event.fqid in self.models:
                del self.models[event.fqid]
            self.model_status[event.fqid] = MODEL_STATUS.RESTORE

        elif isinstance(event, DbUpdateEvent):
            self.models[event.fqid].update(event.field_data)
            self.model_status[event.fqid] = MODEL_STATUS.WRITE

        elif isinstance(event, DbListUpdateEvent):
            for translated_event in event.get_translated_events():
                self.execute_event(translated_event)

        elif isinstance(event, DbDeleteFieldsEvent):
            for field in event.fields:
                if field in self.models[event.fqid]:
                    del self.models[event.fqid][field]
            self.model_status[event.fqid] = MODEL_STATUS.WRITE

        elif isinstance(event, DbDeleteEvent):
            if event.fqid in self.models:
                self.models[event.fqid][META_DELETED] = True
            self.model_status[event.fqid] = MODEL_STATUS.DELETE

        else:
            raise BadCodingError()

    def restore_models(self):
        restored_fqids = [
            fqid
            for fqid, status in self.model_status.items()
            if status == MODEL_STATUS.RESTORE
        ]
        for fqid in restored_fqids:
            self.models[fqid] = self.build_model_ignore_deleted(fqid)
            self.model_status[fqid] = MODEL_STATUS.WRITE

    def build_model_ignore_deleted(self, fqid):
        return self.read_database.build_model_ignore_deleted(fqid)

    def add_position(self):
        for model in self.models.values():
            model[META_POSITION] = self.position

    def write_back(self):
        write_models = {
            fqid: self.models[fqid]
            for fqid, status in self.model_status.items()
            if status in [MODEL_STATUS.WRITE, MODEL_STATUS.DELETE]
        }
        self.read_database.create_or_update_models(write_models)

        # Don't delete the built models from the lookup table since the reader
        # relies on them being there. If the amount of deleted models gets too
        # high and they consume too mush space/slow down the lookup too much,
        # we have to rewrite the reader to differenciate between deleted and
        # non-deleted models and delete the model here from the lookup table.
