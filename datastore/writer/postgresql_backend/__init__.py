from .db_events import (  # noqa
    BaseDbEvent,
    DbCreateEvent,
    DbDeleteEvent,
    DbDeleteFieldsEvent,
    DbListUpdateEvent,
    DbRestoreEvent,
    DbUpdateEvent,
)
from .event_translator import EventTranslator  # noqa
from .sql_database_backend_service import SqlDatabaseBackendService  # noqa
from .sql_occ_locker_backend_service import SqlOccLockerBackendService  # noqa


def setup_di():
    from datastore.shared.di import injector

    from .event_translator import EventTranslatorService

    injector.register(EventTranslator, EventTranslatorService)
