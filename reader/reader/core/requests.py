from dataclasses import dataclass, field
from typing import List, Optional

from shared.core import DeletedModelsBehaviour, Filter


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
