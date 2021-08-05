from .database import Database  # noqa
from .messaging import Messaging  # noqa
from .occ_locker import OccLocker  # noqa
from .write_request import (  # noqa
    BaseRequestEvent,
    CollectionFieldLock,
    CollectionFieldLockWithFilter,
    RequestCreateEvent,
    RequestDeleteEvent,
    RequestRestoreEvent,
    RequestUpdateEvent,
    WriteRequest,
)
from .writer import Writer  # noqa


def setup_di():
    from datastore.shared.di import injector

    from .writer_service import WriterService

    injector.register(Writer, WriterService)
