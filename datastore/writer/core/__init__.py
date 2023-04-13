from .database import Database
from .messaging import Messaging
from .occ_locker import OccLocker
from .write_request import (
    BaseRequestEvent,
    CollectionFieldLock,
    CollectionFieldLockWithFilter,
    RequestCreateEvent,
    RequestDeleteEvent,
    RequestRestoreEvent,
    RequestUpdateEvent,
    WriteRequest,
)
from .writer import Writer


def setup_di():
    from datastore.shared.di import injector

    from .writer_service import WriterService

    injector.register(Writer, WriterService)
