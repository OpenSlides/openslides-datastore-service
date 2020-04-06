from typing import Any, Dict

from shared.core import ReadDatabase, build_fqid
from shared.di import service_as_factory
from shared.postgresql_backend.connection_handler import ConnectionHandler

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

    connection: ConnectionHandler
    database: ReadDatabase

    def get(self, request: GetRequest) -> Dict[str, Any]:
        with self.database.get_context():
            model = self.database.get(
                request.fqid, request.mapped_fields, request.get_deleted_models
            )
        return model

    def get_many(self, request: GetManyRequest):
        with self.database.get_context():
            result = self.database.get_many(
                [
                    build_fqid(part.collection, id)
                    for part in request.requests
                    for id in part.ids
                ],
                {
                    part.collection: part.mapped_fields + request.mapped_fields
                    for part in request.requests
                },
                request.get_deleted_models,
            )
        return result

    def get_all(self, request: GetAllRequest):
        with self.database.get_context():
            result = self.database.get_all(
                request.collection, request.mapped_fields, request.get_deleted_models
            )
        return result

    def filter(self, request: FilterRequest):
        with self.database.get_context():
            result = self.database.filter(
                request.collection, request.filter, request.mapped_fields
            )
        return result

    def exists(self, request: AggregateRequest):
        count = self.count(request)
        return {"exists": count["count"] > 0, "position": 0}

    def count(self, request: AggregateRequest):
        return self.aggregate(request.collection, request.filter, "count", "fqid")

    def min(self, request: MinMaxRequest):
        return self.aggregate(request.collection, request.filter, "min", request.field)

    def max(self, request: MinMaxRequest):
        return self.aggregate(request.collection, request.filter, "max", request.field)

    def aggregate(self, collection, filter, function, field):
        with self.database.get_context():
            value = self.database.aggregate(collection, filter, (function, field))
        return {function: value, "position": 0}
