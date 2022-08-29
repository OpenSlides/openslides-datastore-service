from dataclasses import dataclass, field
from typing import List, Optional, Union, cast

from datastore.shared.postgresql_backend.sql_query_helper import (
    VALID_AGGREGATE_CAST_TARGETS,
)
from datastore.shared.typing import Collection, Field, Fqfield, Fqid, Id, Position
from datastore.shared.util import (
    DeletedModelsBehaviour,
    Filter,
    MappedFields,
    SelfValidatingDataclass,
    collection_from_fqid,
    field_from_fqfield,
    fqid_from_collection_and_id,
    fqid_from_fqfield,
)


@dataclass
class GetRequest(SelfValidatingDataclass):
    fqid: Fqid
    mapped_fields: List[Field] = field(default_factory=list)
    position: Optional[Position] = None
    get_deleted_models: DeletedModelsBehaviour = DeletedModelsBehaviour.NO_DELETED

    def build_mapped_fields(self) -> MappedFields:
        mapped_fields = MappedFields()
        _mapped_fields = list(set(self.mapped_fields))
        mapped_fields.per_fqid = {self.fqid: _mapped_fields}
        mapped_fields.unique_fields = _mapped_fields
        mapped_fields.collections = [collection_from_fqid(self.fqid)]
        mapped_fields.post_init()
        return mapped_fields


@dataclass
class GetManyRequestPart(SelfValidatingDataclass):
    collection: Collection
    ids: List[Id]
    mapped_fields: List[Field] = field(default_factory=list)


@dataclass
class GetManyRequest(SelfValidatingDataclass):
    requests: Union[List[GetManyRequestPart], List[Fqfield]]
    mapped_fields: List[Field] = field(default_factory=list)
    position: Optional[Position] = None
    get_deleted_models: DeletedModelsBehaviour = DeletedModelsBehaviour.NO_DELETED

    def build_mapped_fields(self) -> MappedFields:
        mapped_fields = MappedFields()
        unique_fields_set = set()
        collections_set = set()
        if isinstance(self.requests[0], GetManyRequestPart):
            unique_fields_set.update(self.mapped_fields)
            requests = cast(List[GetManyRequestPart], self.requests)
            for part in requests:
                unique_fields_set.update(part.mapped_fields)
                collections_set.add(part.collection)
                for id in part.ids:
                    fqid = fqid_from_collection_and_id(part.collection, str(id))
                    mapped_fields.per_fqid[fqid].extend(
                        part.mapped_fields + self.mapped_fields
                    )
        else:
            fqfield_requests = cast(List[str], self.requests)
            for fqfield in fqfield_requests:
                fqid = fqid_from_fqfield(fqfield)
                collections_set.add(collection_from_fqid(fqid))
                field = field_from_fqfield(fqfield)
                mapped_fields.per_fqid[fqid].append(field)
                unique_fields_set.add(field)
        mapped_fields.unique_fields = list(unique_fields_set)
        mapped_fields.collections = list(collections_set)
        mapped_fields.post_init()
        return mapped_fields


@dataclass
class GetAllRequest(SelfValidatingDataclass):
    collection: Collection
    mapped_fields: List[Field] = field(default_factory=list)
    get_deleted_models: DeletedModelsBehaviour = DeletedModelsBehaviour.NO_DELETED


@dataclass
class GetEverythingRequest(SelfValidatingDataclass):
    get_deleted_models: DeletedModelsBehaviour = DeletedModelsBehaviour.NO_DELETED


@dataclass
class FilterRequest(SelfValidatingDataclass):
    collection: Collection
    filter: Filter
    mapped_fields: List[Field] = field(default_factory=list)


@dataclass
class AggregateRequest(SelfValidatingDataclass):
    collection: Collection
    filter: Filter


@dataclass
class MinMaxRequest(SelfValidatingDataclass):
    collection: Collection
    filter: Filter
    field: Field
    type: str = VALID_AGGREGATE_CAST_TARGETS[0]


@dataclass
class HistoryInformationRequest(SelfValidatingDataclass):
    fqids: List[Fqid]
