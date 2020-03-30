from typing import Any, Dict, List, cast

from reader.core.reader import CountResult, ExistsResult, MaxResult, MinResult
from reader.core.requests import GetManyRequestPart
from shared.di import service_as_factory
from shared.postgresql_backend import ConnectionHandler
from shared.services import ReadDatabase
from shared.services.read_database import (
    AggregateFilterQueryFieldsParameters,
    BaseAggregateFilterQueryFieldsParameters,
    CountFilterQueryFieldsParameters,
)
from shared.typing import Model
from shared.util import (
    DeletedModelsBehaviour,
    Filter,
    build_fqid,
    get_exception_for_deleted_models_behaviour,
)
from shared.util.key_transforms import field_from_fqfield, fqid_from_fqfield

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
            if request.position:
                # if a position is given, first test if the model is in the correct
                # state to prevent the unneccessary building of the model if it's not
                fqids = self.filter_fqids_by_deleted_status(
                    [request.fqid], request.position, request.get_deleted_models
                )
                if not len(fqids):
                    raise get_exception_for_deleted_models_behaviour(
                        request.fqid, request.get_deleted_models
                    )

                model = self.database.build_model_ignore_deleted(
                    request.fqid, request.position
                )
                model = self.apply_mapped_fields(model, request.mapped_fields)
            else:
                model = self.database.get(
                    request.fqid, request.mapped_fields, request.get_deleted_models
                )
        return model

    def get_many(self, request: GetManyRequest) -> Dict[str, Model]:
        with self.database.get_context():
            if isinstance(request.requests[0], GetManyRequestPart):
                requests = cast(List[GetManyRequestPart], request.requests)
                mapped_fields_per_fqid = {
                    build_fqid(part.collection, str(id)): part.mapped_fields
                    + request.mapped_fields
                    for part in requests
                    for id in part.ids
                }
            else:
                fqfield_requests = cast(List[str], request.requests)
                mapped_fields_per_fqid = {
                    fqid_from_fqfield(fqfield): [field_from_fqfield(fqfield)]
                    for fqfield in fqfield_requests
                }

            fqids = list(mapped_fields_per_fqid.keys())

            if request.position:
                fqids = self.filter_fqids_by_deleted_status(
                    fqids, request.position, request.get_deleted_models
                )
                result = self.database.build_models_ignore_deleted(
                    fqids, request.position
                )
                result = self.apply_mapped_fields_multi(result, mapped_fields_per_fqid)
            else:
                result = self.database.get_many(
                    fqids, mapped_fields_per_fqid, request.get_deleted_models,
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
        res = self.aggregate(
            request.collection, request.filter, CountFilterQueryFieldsParameters()
        )
        return cast(CountResult, res)

    def minmax(self, request: MinMaxRequest, mode: str) -> Dict[str, Any]:
        params = AggregateFilterQueryFieldsParameters(mode, request.field, request.type)
        return self.aggregate(request.collection, request.filter, params)

    def min(self, request: MinMaxRequest) -> MinResult:
        res = self.minmax(request, "min")
        return cast(MinResult, res)

    def max(self, request: MinMaxRequest) -> MaxResult:
        res = self.minmax(request, "max")
        return cast(MaxResult, res)

    def aggregate(
        self,
        collection: str,
        filter: Filter,
        fields_params: BaseAggregateFilterQueryFieldsParameters,
    ) -> Dict[str, Any]:
        with self.database.get_context():
            result = self.database.aggregate(collection, filter, fields_params)
        return result

    def filter_fqids_by_deleted_status(
        self,
        fqids: List[str],
        position: int,
        get_deleted_models: DeletedModelsBehaviour,
    ) -> List[str]:
        if get_deleted_models == DeletedModelsBehaviour.ALL_MODELS:
            return fqids
        else:
            deleted_map = self.database.get_deleted_status(fqids, position)
            return [
                fqid
                for fqid in fqids
                if fqid in deleted_map
                and deleted_map[fqid]
                == (get_deleted_models == DeletedModelsBehaviour.ONLY_DELETED)
            ]

    def apply_mapped_fields(self, model: Model, mapped_fields: List[str]) -> Model:
        if not mapped_fields or not len(mapped_fields):
            return model
        return {field: model[field] for field in mapped_fields if field in model}

    def apply_mapped_fields_multi(
        self, models: Dict[str, Model], mapped_fields_per_fqid: Dict[str, List[str]],
    ) -> Dict[str, Model]:
        if not mapped_fields_per_fqid or not len(mapped_fields_per_fqid):
            return models
        return {
            fqid: self.apply_mapped_fields(model, mapped_fields_per_fqid.get(fqid, []))
            for fqid, model in models.items()
        }
