from typing import Any, Dict, List

from reader.core.reader import CountResult, ExistsResult, MaxResult, MinResult
from shared.core import (
    DeletedModelsBehaviour,
    ModelDoesNotExist,
    ModelNotDeleted,
    ReadDatabase,
    build_fqid,
    collection_from_fqid,
)
from shared.di import service_as_factory
from shared.postgresql_backend import ConnectionHandler
from shared.util import Model

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

    def get(self, request: GetRequest) -> Model:
        with self.database.get_context():
            deleted = self.database.is_deleted(request.fqid, request.position)
            if (
                deleted
                and request.get_deleted_models == DeletedModelsBehaviour.NO_DELETED
            ):
                raise ModelDoesNotExist(request.fqid)
            if (
                not deleted
                and request.get_deleted_models == DeletedModelsBehaviour.ONLY_DELETED
            ):
                raise ModelNotDeleted(request.fqid)

            if request.position:
                model = self.database.build_model_ignore_deleted(
                    request.fqid, request.position
                )
                model = self.apply_mapped_fields(model, request.mapped_fields)
            else:
                model = self.database.get(request.fqid, request.mapped_fields)
        return model

    def get_many(self, request: GetManyRequest) -> Dict[str, Model]:
        with self.database.get_context():
            fqids = [
                build_fqid(part.collection, id)
                for part in request.requests
                for id in part.ids
            ]
            mapped_fields_per_collection = {
                part.collection: part.mapped_fields + request.mapped_fields
                for part in request.requests
            }

            if request.position:
                deleted_map = self.database.get_deleted_status(fqids, request.position)
                if request.get_deleted_models != DeletedModelsBehaviour.ALL_MODELS:
                    fqids = [
                        fqid
                        for fqid in fqids
                        if fqid in deleted_map
                        and deleted_map[fqid]
                        == (
                            request.get_deleted_models
                            == DeletedModelsBehaviour.ONLY_DELETED
                        )
                    ]

                result = self.database.build_models_ignore_deleted(
                    fqids, request.position
                )
                result = self.apply_mapped_fields_multi(
                    result, mapped_fields_per_collection
                )
            else:
                result = self.database.get_many(
                    fqids, mapped_fields_per_collection, request.get_deleted_models,
                )
        return result

    def get_all(self, request: GetAllRequest) -> List[Model]:
        with self.database.get_context():
            result = self.database.get_all(
                request.collection, request.mapped_fields, request.get_deleted_models
            )
        return result

    def filter(self, request: FilterRequest) -> List[Model]:
        with self.database.get_context():
            result = self.database.filter(
                request.collection, request.filter, request.mapped_fields
            )
        return result

    def exists(self, request: AggregateRequest) -> ExistsResult:
        count = self.count(request)
        return {"exists": count["count"] > 0, "position": count["position"]}

    def count(self, request: AggregateRequest) -> CountResult:
        return self.aggregate(request.collection, request.filter, "count")

    def minmax(self, request: MinMaxRequest, mode: str) -> Dict[str, Any]:
        return self.aggregate(
            request.collection, request.filter, mode, request.field, request.type
        )

    def min(self, request: MinMaxRequest) -> MinResult:
        return self.minmax(request, "min")

    def max(self, request: MinMaxRequest) -> MaxResult:
        return self.minmax(request, "max")

    def aggregate(
        self, collection, filter, function, field=None, type=None
    ) -> Dict[str, Any]:
        with self.database.get_context():
            result = self.database.aggregate(
                collection, filter, (function, field, type)
            )
        return result

    def apply_mapped_fields(self, model: Model, mapped_fields: List[str]) -> Model:
        if not mapped_fields or not len(mapped_fields):
            return model
        return {field: model[field] for field in mapped_fields if field in model}

    def apply_mapped_fields_multi(
        self,
        models: Dict[str, Model],
        mapped_fields_per_collection: Dict[str, List[str]],
    ) -> Dict[str, Model]:
        if not mapped_fields_per_collection or not len(mapped_fields_per_collection):
            return models
        return {
            fqid: self.apply_mapped_fields(
                model, mapped_fields_per_collection[collection_from_fqid(fqid)]
            )
            for fqid, model in models.items()
        }
