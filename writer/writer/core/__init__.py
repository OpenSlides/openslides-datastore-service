from .database import Database  # noqa
from .db_events import (  # noqa
    BaseDbEvent,
    DbCreateEvent,
    DbDeleteEvent,
    DbDeleteFieldsEvent,
    DbRestoreEvent,
    DbUpdateEvent,
)
from .messaging import Messaging  # noqa
from .occ_locker import OccLocker  # noqa
from .write_request import (  # noqa
    BaseRequestEvent,
    RequestCreateEvent,
    RequestDeleteEvent,
    RequestRestoreEvent,
    RequestUpdateEvent,
    WriteRequest,
)
from .writer import Writer  # noqa


def setup_di():
    from shared.di import injector
    from .writer_service import WriterService
    from .event_executor import EventExecutor, EventExecutorService
    from .event_translator import EventTranslator, EventTranslatorService

    injector.register(EventTranslator, EventTranslatorService)
    injector.register(EventExecutor, EventExecutorService)
    injector.register(Writer, WriterService)
