from dataclasses import dataclass, field
from typing import List, Optional

from shared.core import DeletedModelsBehaviour, Filter
from shared.postgresql_backend.sql_read_database_backend_service import (
    VALID_AGGREGATE_CAST_TARGETS,
)


@dataclass
class GetRequest:
    fqid: str
    mapped_fields: List[str] = field(default_factory=list)
    position: Optional[int] = None
    get_deleted_models: Optional[
        DeletedModelsBehaviour
    ] = DeletedModelsBehaviour.NO_DELETED


@dataclass
class GetManyRequestPart:
    collection: str
    ids: List[int]
    mapped_fields: List[str] = field(default_factory=list)


@dataclass
class GetManyRequest:
    requests: List[GetManyRequestPart]
    mapped_fields: List[str] = field(default_factory=list)
    position: Optional[int] = None
    get_deleted_models: Optional[
        DeletedModelsBehaviour
    ] = DeletedModelsBehaviour.NO_DELETED


@dataclass
class GetAllRequest:
    collection: str
    mapped_fields: List[str] = field(default_factory=list)
    get_deleted_models: Optional[
        DeletedModelsBehaviour
    ] = DeletedModelsBehaviour.NO_DELETED


@dataclass
class FilterRequest:
    collection: str
    filter: Filter
    mapped_fields: List[str] = field(default_factory=list)


@dataclass
class AggregateRequest:
    collection: str
    filter: Filter


@dataclass
class MinMaxRequest:
    collection: str
    filter: Filter
    field: str
    type: str = VALID_AGGREGATE_CAST_TARGETS[0]
