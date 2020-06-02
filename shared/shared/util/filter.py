from dataclasses import dataclass
from typing import Any, List, Literal, Union

from shared.typing import Field

from .self_validating_dataclass import SelfValidatingDataclass


@dataclass
class FilterOperator(SelfValidatingDataclass):
    field: Field
    operator: Literal["=", "!=", "<", ">", ">=", "<="]
    value: Any


@dataclass
class Not:
    not_filter: "Filter"


@dataclass
class And:
    and_filter: List["Filter"]


@dataclass
class Or:
    or_filter: List["Filter"]


Filter = Union[And, Or, Not, FilterOperator]
