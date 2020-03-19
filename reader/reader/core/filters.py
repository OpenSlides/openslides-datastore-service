from typing import Any, List, Literal, TypedDict, Union


class FilterOperator(TypedDict):
    field: str
    value: Any
    operator: Literal["==", "!=", "<", ">", ">=", "<="]


# TODO: mypy doesn't seem to support this kind of recursive typing.


class Not(TypedDict):
    not_filter: "Filter"  # type: ignore


class And(TypedDict):
    and_filter: List["Filter"]  # type: ignore


class Or(TypedDict):
    or_filter: List["Filter"]  # type: ignore


Filter = Union[And, Or, Not, FilterOperator]  # type: ignore
