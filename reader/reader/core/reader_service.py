from shared.di import service_as_factory

from .requests import (
    AggregateRequest,
    FilterRequest,
    GetAllRequest,
    GetManyRequest,
    GetRequest,
    MinMaxRequest,
)


@service_as_factory
class ReaderService:
    def get(self, request: GetRequest):
        return request.fqid

    def get_many(self, request: GetManyRequest):
        pass

    def get_all(self, request: GetAllRequest):
        pass

    def filter(self, request: FilterRequest):
        pass

    def exists(self, request: AggregateRequest):
        pass

    def count(self, request: AggregateRequest):
        pass

    def min(self, request: MinMaxRequest):
        pass

    def max(self, request: MinMaxRequest):
        pass
