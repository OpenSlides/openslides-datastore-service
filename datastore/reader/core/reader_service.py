from collections import defaultdict
from typing import Any, ContextManager, Dict, List, cast


from datastore.reader.core.reader import (
    CountResult,
    ExistsResult,
    FilterResult,
    MaxResult,
    MinResult,
)
from datastore.reader.core.requests import GetManyRequestPart
from datastore.shared.di import service_as_factory
from datastore.shared.postgresql_backend import ConnectionHandler, retry_on_db_failure
from datastore.shared.services import HistoryInformation, ReadDatabase
from datastore.shared.services.read_database import (
    AggregateFilterQueryFieldsParameters,
    BaseAggregateFilterQueryFieldsParameters,
    CountFilterQueryFieldsParameters,
)
from datastore.shared.typing import Collection, Fqid, Id, Model
from datastore.shared.util.otel import make_span
from datastore.shared.util import (
    DeletedModelsBehaviour,
    Filter,
    collection_from_fqid,
    fqid_from_collection_and_id,
    get_exception_for_deleted_models_behaviour,
)
from datastore.shared.util.key_transforms import (
    collection_and_id_from_fqid,
    field_from_fqfield,
    fqid_from_fqfield,
)

from .requests import (
    AggregateRequest,
    FilterRequest,
    GetAllRequest,
    GetEverythingRequest,
    GetManyRequest,
    GetRequest,
    HistoryInformationRequest,
    MinMaxRequest,
)


@service_as_factory
class ReaderService:

    connection: ConnectionHandler
    database: ReadDatabase

    def get_database_context(self) -> ContextManager[None]:
        return self.database.get_context()

    @retry_on_db_failure
    def get(self, request: GetRequest) -> Model:
        with make_span("get request"):
            if request.position:
                # if a position is given, first test if the model is in the correct
                # state to prevent the unnecessary building of the model if it's not
                with make_span("check deleted status for position-based request"):
                    fqids = self.filter_fqids_by_deleted_status(
                        [request.fqid], request.position, request.get_deleted_models
                    )
                    if not len(fqids):
                        raise get_exception_for_deleted_models_behaviour(
                            request.fqid, request.get_deleted_models
                        )

                    with make_span("build model for position"):
                        model = self.database.build_model_ignore_deleted(
                            request.fqid, request.position
                        )
                with make_span("apply mapped fields"):
                    model = self.apply_mapped_fields(model, request.mapped_fields)
            else:
                with make_span("get from database"):
                    model = self.database.get(
                        request.fqid, request.mapped_fields, request.get_deleted_models
                    )
        return model

    @retry_on_db_failure
    def get_many(self, request: GetManyRequest) -> Dict[Collection, Dict[Id, Model]]:
        with make_span("get_many request"):
            with make_span("gather mapped fields per fqid"):
                mapped_fields_per_fqid: Dict[str, List[str]] = defaultdict(list)
                if isinstance(request.requests[0], GetManyRequestPart):
                    requests = cast(List[GetManyRequestPart], request.requests)
                    for part in requests:
                        for id in part.ids:
                            fqid = fqid_from_collection_and_id(part.collection, str(id))
                            mapped_fields_per_fqid[fqid].extend(
                                part.mapped_fields + request.mapped_fields
                            )
                else:
                    fqfield_requests = cast(List[str], request.requests)
                    for fqfield in fqfield_requests:
                        fqid = fqid_from_fqfield(fqfield)
                        mapped_fields_per_fqid[fqid].append(
                            field_from_fqfield(fqfield)
                        )

            fqids = list(mapped_fields_per_fqid.keys())

            with make_span("call database"):
                if request.position:
                    fqids = self.filter_fqids_by_deleted_status(
                        fqids, request.position, request.get_deleted_models
                    )
                    result = self.database.build_models_ignore_deleted(fqids, request.position)
                    result = self.apply_mapped_fields_multi(result, mapped_fields_per_fqid)
                else:
                    result = self.database.get_many(
                        fqids,
                        mapped_fields_per_fqid,
                        request.get_deleted_models,
                    )

            with make_span("change mapping"):
                # change mapping fqid->model to collection->id->model
                final: Dict[str, Dict[int, Model]] = defaultdict(dict)
                for fqid, model in result.items():
                    collection, id = collection_and_id_from_fqid(fqid)
                    final[collection][id] = model

                with make_span("add back empty collections"):
                    # add back empty collections
                    for fqid in mapped_fields_per_fqid.keys():
                        collection = collection_from_fqid(fqid)
                        if not final[collection]:
                            final[collection] = {}
        return final

    @retry_on_db_failure
    def get_all(self, request: GetAllRequest) -> Dict[Id, Model]:
        with make_span("get_all request"):
            models = self.database.get_all(
                request.collection, request.mapped_fields, request.get_deleted_models
            )
        return models

    @retry_on_db_failure
    def get_everything(
        self, request: GetEverythingRequest
    ) -> Dict[Collection, Dict[Id, Model]]:
        return self.database.get_everything(request.get_deleted_models)

    @retry_on_db_failure
    def filter(self, request: FilterRequest) -> FilterResult:
        with make_span("filter request"):
            data = self.database.filter(
                request.collection, request.filter, request.mapped_fields
            )
            position = self.database.get_max_position()
        return {
            "data": data,
            "position": position,
        }

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

    @retry_on_db_failure
    def aggregate(
        self,
        collection: str,
        filter: Filter,
        fields_params: BaseAggregateFilterQueryFieldsParameters,
    ) -> Dict[str, Any]:
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
        return {
            field: model[field]
            for field in mapped_fields
            if field in model and model[field] is not None
        }

    def apply_mapped_fields_multi(
        self,
        models: Dict[str, Model],
        mapped_fields_per_fqid: Dict[str, List[str]],
    ) -> Dict[str, Model]:
        if not mapped_fields_per_fqid or not len(mapped_fields_per_fqid):
            return models
        return {
            fqid: self.apply_mapped_fields(model, mapped_fields_per_fqid.get(fqid, []))
            for fqid, model in models.items()
        }

    @retry_on_db_failure
    def history_information(
        self, request: HistoryInformationRequest
    ) -> Dict[Fqid, List[HistoryInformation]]:
        return self.database.get_history_information(request.fqids)
