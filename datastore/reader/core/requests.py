from dataclasses import dataclass, field
from typing import List, Optional, Union

from datastore.shared.postgresql_backend.sql_query_helper import (
    VALID_AGGREGATE_CAST_TARGETS,
)
from datastore.shared.typing import Collection, Field, Fqfield, Fqid, Id, Position
from datastore.shared.util import (
    DeletedModelsBehaviour,
    Filter,
    SelfValidatingDataclass,
)


@dataclass
class GetRequest(SelfValidatingDataclass):
    fqid: Fqid
    mapped_fields: List[Field] = field(default_factory=list)
    position: Optional[Position] = None
    get_deleted_models: DeletedModelsBehaviour = DeletedModelsBehaviour.NO_DELETED


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
