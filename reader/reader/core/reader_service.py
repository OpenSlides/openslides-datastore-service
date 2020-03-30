from typing import Any, Dict, List, Optional

from flask import jsonify

from shared.core.exceptions import ModelDoesNotExist
from shared.core.key_transforms import build_fqid
from shared.core.read_database import ReadDatabase
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

    database: ReadDatabase

    def get(self, request: GetRequest) -> Dict[str, Any]:
        with self.database.get_context():
            models = self.database.get_models_filtered(
                [request.fqid], request.get_deleted_models
            )
            if request.fqid not in models:
                raise ModelDoesNotExist(request.fqid)
            return self.apply_mapped_fields(models[request.fqid], request.mapped_fields)

    def get_many(self, request: GetManyRequest):
        result_set = []
        with self.database.get_context():
            for part in request.requests:
                fqids = [build_fqid(part.collection, id) for id in part.ids]
                models = self.database.get_models_filtered(
                    fqids, request.get_deleted_models
                )

                result_set += self.apply_mapped_fields_multi(
                    models.values(), part.mapped_fields + request.mapped_fields
                )
        return jsonify(result_set)

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
