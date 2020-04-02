from typing import Any, Dict, List, Optional

from shared.core import ReadDatabase, build_fqid, Filter
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
            model = self.database.get(request.fqid, request.get_deleted_models)
        return self.apply_mapped_fields(model, request.mapped_fields)

    def get_many(self, request: GetManyRequest):
        result_list = []
        with self.database.get_context():
            for part in request.requests:
                fqids = [build_fqid(part.collection, id) for id in part.ids]
                models = self.database.get_many(fqids, request.get_deleted_models)

                result_list += self.apply_mapped_fields_multi(
                    models.values(), part.mapped_fields + request.mapped_fields
                )
        return result_list

    def get_all(self, request: GetAllRequest):
        with self.database.get_context():
            result = self.database.get_all(
                request.collection, request.get_deleted_models
            )
        return self.apply_mapped_fields_multi(result, request.mapped_fields)

    def filter(self, request: FilterRequest):
        models = self.get_filtered_models(request.collection, request.filter)
        return self.apply_mapped_fields_multi(models, request.mapped_fields)

    def get_filtered_models(self, collection: str, filter: Filter):
        with self.database.get_context():
            result = self.database.filter(collection, filter)
        return result

    def exists(self, request: AggregateRequest):
        models = self.get_filtered_models(request.collection, request.filter)
        return {"exists": len(models) > 0, "position": 0}

    def count(self, request: AggregateRequest):
        # TODO: maybe better to count via  sql?
        models = self.get_filtered_models(request.collection, request.filter)
        return {"count": len(models), "position": 0}

    def min(self, request: MinMaxRequest):
        with self.database.get_context():
            result = self.database.filter(request.collection, request.filter, ("MIN", request.field))
        return {"min": result[0], "position": 0}

    def max(self, request: MinMaxRequest):
        pass

    def apply_mapped_fields_multi(
        self, models: List[Dict[str, Any]], mapped_fields: Optional[List[str]]
    ) -> List[Dict[str, Any]]:
        if not mapped_fields:
            return models
        return [self.apply_mapped_fields(model, mapped_fields) for model in models]

    def apply_mapped_fields(
        self, model: Dict[str, Any], mapped_fields: Optional[List[str]]
    ) -> Dict[str, Any]:
        if not mapped_fields:
            return model
        return {field: model[field] for field in mapped_fields if field in model}
