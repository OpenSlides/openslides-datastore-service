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


filter_definitions_schema = {
    "filter": {
        "anyOf": [
            {"$ref": "#/definitions/filter_operator"},
            {"$ref": "#/definitions/not_filter"},
            {"$ref": "#/definitions/and_filter"},
            {"$ref": "#/definitions/or_filter"},
        ],
    },
    "filter_operator": {
        "type": "object",
        "properties": {
            "field": {"type": "string"},
            "value": {},
            "operator": {"type": "string", "enum": ["=", "!=", "<", ">", ">=", "<="]},
        },
        "required": ["field", "value", "operator"],
    },
    "not_filter": {
        "type": "object",
        "properties": {"not_filter": {"$ref": "#/definitions/filter"}},
        "required": ["not_filter"],
    },
    "and_filter": {
        "type": "object",
        "properties": {
            "and_filter": {
                "type": "array",
                "items": {"$ref": "#/definitions/filter"},
                "minItems": 2,
            },
        },
        "required": ["and_filter"],
    },
    "or_filter": {
        "type": "object",
        "properties": {
            "or_filter": {
                "type": "array",
                "items": {"$ref": "#/definitions/filter"},
                "minItems": 2,
            },
        },
        "required": ["or_filter"],
    },
}
