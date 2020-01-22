from .database import Database  # noqa
from .db_events import (  # noqa
    BaseDbEvent,
    DbCreateEvent,
    DbDeleteEvent,
    DbDeleteFieldsEvent,
    DbRestoreEvent,
    DbUpdateEvent,
)
from .exceptions import (  # noqa
    InvalidFormat,
    ModelDoesNotExist,
    ModelExists,
    ModelLocked,
    ModelNotDeleted,
)
from .key_transforms import (  # noqa
    collectionfield_from_fqid_and_field,
    fqfield_from_fqid_and_field,
    fqid_and_field_from_fqfield,
)
from .messaging import Messaging  # noqa
from .occ_locker import OccLocker  # noqa
from .read_database import ReadDatabase  # noqa
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
    from writer.di import injector
    from .writer_service import WriterService
    from .event_executor import EventExecutor, EventExecutorService
    from .event_translator import EventTranslator, EventTranslatorService

    injector.register(EventTranslator, EventTranslatorService)
    injector.register(EventExecutor, EventExecutorService)
    injector.register(Writer, WriterService)
