from dataclasses import dataclass, field
from typing import List, Optional

from shared.core import DeletedModelsBehaviour, Filter
from shared.core.self_validating_dataclass import SelfValidatingDataclass
from shared.postgresql_backend.sql_query_helper import VALID_AGGREGATE_CAST_TARGETS
from shared.util import Collection, Field, Fqid, Id, Position


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
    requests: List[GetManyRequestPart]
    mapped_fields: List[Field] = field(default_factory=list)
    position: Optional[Position] = None
    get_deleted_models: DeletedModelsBehaviour = DeletedModelsBehaviour.NO_DELETED


@dataclass
class GetAllRequest(SelfValidatingDataclass):
    collection: Collection
    mapped_fields: List[Field] = field(default_factory=list)
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
