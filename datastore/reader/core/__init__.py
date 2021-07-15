from .reader import Reader
from .requests import (  # noqa
    AggregateRequest,
    FilterRequest,
    GetAllRequest,
    GetEverythingRequest,
    GetManyRequest,
    GetManyRequestPart,
    GetRequest,
    MinMaxRequest,
)


def setup_di():
    from datastore.shared.di import injector

    from .reader_service import ReaderService

    injector.register(Reader, ReaderService)
