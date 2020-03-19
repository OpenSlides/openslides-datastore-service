from dataclasses import dataclass
from enum import Enum
from typing import List, Optional

from .filters import Filter


class DeletedModelsBehaviour(Enum):
    NO_DELETED = 1
    ONLY_DELETED = 2
    ALL_MODELS = 3


@dataclass
class GetRequest:
    fqid: str
    position: Optional[int] = None
    mapped_fields: Optional[List[str]] = None
    get_deleted_models: Optional[
        DeletedModelsBehaviour
    ] = DeletedModelsBehaviour.NO_DELETED


@dataclass
class GetManyRequestPart:
    collection: str
    ids: List[int]
    mapped_fields: Optional[List[str]] = None


@dataclass
class GetManyRequest:
    requests: List[GetManyRequestPart]
    position: Optional[int] = None
    mapped_fields: Optional[List[str]] = None
    get_deleted_models: Optional[
        DeletedModelsBehaviour
    ] = DeletedModelsBehaviour.NO_DELETED


@dataclass
class GetAllRequest:
    collection: str
    mapped_fields: Optional[List[str]] = None
    get_deleted_models: Optional[
        DeletedModelsBehaviour
    ] = DeletedModelsBehaviour.NO_DELETED


@dataclass
class FilterRequest:
    collection: str
    filter: Filter
    mapped_fields: Optional[List[str]] = None


@dataclass
class AggregateRequest:
    collection: str
    filter: Filter


@dataclass
class MinMaxRequest:
    collection: str
    filter: Filter
    field: str
