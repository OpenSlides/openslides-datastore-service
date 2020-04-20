from dataclasses import dataclass
from typing import Any, List, Literal, Union


@dataclass
class FilterOperator:
    field: str
    operator: Literal["=", "!=", "<", ">", ">=", "<="]
    value: Any


# TODO: mypy doesn't seem to support this kind of recursive typing.


@dataclass
class Not:
    not_filter: "Filter"  # type: ignore


@dataclass
class And:
    and_filter: List["Filter"]  # type: ignore


@dataclass
class Or:
    or_filter: List["Filter"]  # type: ignore


Filter = Union[And, Or, Not, FilterOperator]  # type: ignore