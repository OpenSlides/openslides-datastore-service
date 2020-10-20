from dataclasses import dataclass
from enum import Enum
from typing import Callable, Dict, Type

import fastjsonschema

from reader.core.requests import (
    AggregateRequest,
    FilterRequest,
    GetAllRequest,
    GetEverythingRequest,
    GetManyRequest,
    GetRequest,
    MinMaxRequest,
)
from shared.flask_frontend import unify_urls
from shared.postgresql_backend.sql_query_helper import VALID_AGGREGATE_CAST_TARGETS
from shared.util import DeletedModelsBehaviour


URL_PREFIX = "/internal/datastore/reader/"


class Route(str, Enum):
    GET = "get"
    GET_MANY = "get_many"
    GET_ALL = "get_all"
    GET_EVERYTHING = "get_everything"
    FILTER = "filter"
    EXISTS = "exists"
    COUNT = "count"
    MIN = "min"
    MAX = "max"

    @property
    def URL(self):
        return unify_urls(URL_PREFIX, self.value)


deleted_models_behaviour_list = list(
    behaviour.value for behaviour in DeletedModelsBehaviour
)


get_schema = fastjsonschema.compile(
    {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "properties": {
            "fqid": {"type": "string"},
            "position": {"type": "integer"},
            "mapped_fields": {"type": "array", "items": {"type": "string"}},
            "get_deleted_models": {
                "type": "integer",
                "enum": deleted_models_behaviour_list,
            },
        },
        "required": ["fqid"],
    }
)


get_many_schema = fastjsonschema.compile(
    {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "properties": {
            "requests": {
                "oneOf": [
                    {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "collection": {"type": "string"},
                                "ids": {"type": "array", "items": {"type": "integer"}},
                                "mapped_fields": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                },
                            },
                            "required": ["collection", "ids"],
                        },
                    },
                    {"type": "array", "items": {"type": "string"}},
                ],
            },
            "position": {"type": "integer"},
            "mapped_fields": {"type": "array", "items": {"type": "string"}},
            "get_deleted_models": {
                "type": "integer",
                "enum": deleted_models_behaviour_list,
            },
        },
        "required": ["requests"],
    }
)

get_all_schema = fastjsonschema.compile(
    {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "properties": {
            "collection": {"type": "string"},
            "mapped_fields": {"type": "array", "items": {"type": "string"}},
            "get_deleted_models": {
                "type": "integer",
                "enum": deleted_models_behaviour_list,
            },
        },
        "required": ["collection"],
    }
)

get_everything_schema = fastjsonschema.compile(
    {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "properties": {
            "get_deleted_models": {
                "type": "integer",
                "enum": deleted_models_behaviour_list,
            },
        },
    }
)

# for reuse in filter_schema and aggregate_schema
filter_definitions = {
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

filter_schema = fastjsonschema.compile(
    {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "definitions": filter_definitions,
        "properties": {
            "collection": {"type": "string"},
            "filter": {"$ref": "#/definitions/filter"},
            "mapped_fields": {"type": "array", "items": {"type": "string"}},
        },
        "required": ["collection", "filter"],
    }
)

aggregate_schema = fastjsonschema.compile(
    {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "definitions": filter_definitions,
        "properties": {
            "collection": {"type": "string"},
            "filter": {"$ref": "#/definitions/filter"},
        },
        "required": ["collection", "filter"],
    }
)

minmax_schema = fastjsonschema.compile(
    {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "definitions": filter_definitions,
        "properties": {
            "collection": {"type": "string"},
            "filter": {"$ref": "#/definitions/filter"},
            "field": {"type": "string"},
            "type": {"type": "string", "enum": VALID_AGGREGATE_CAST_TARGETS},
        },
        "required": ["collection", "filter", "field"],
    }
)


@dataclass
class RouteConfiguration:
    schema: Callable
    request_class: Type
    dev_only: bool = False


# maps all available routes to the respective schema
route_configurations: Dict[Route, RouteConfiguration] = {
    Route.GET: RouteConfiguration(schema=get_schema, request_class=GetRequest),
    Route.GET_MANY: RouteConfiguration(
        schema=get_many_schema, request_class=GetManyRequest
    ),
    Route.GET_ALL: RouteConfiguration(
        schema=get_all_schema, request_class=GetAllRequest
    ),
    Route.GET_EVERYTHING: RouteConfiguration(
        schema=get_everything_schema, request_class=GetEverythingRequest, dev_only=True
    ),
    Route.FILTER: RouteConfiguration(schema=filter_schema, request_class=FilterRequest),
    Route.EXISTS: RouteConfiguration(
        schema=aggregate_schema, request_class=AggregateRequest
    ),
    Route.COUNT: RouteConfiguration(
        schema=aggregate_schema, request_class=AggregateRequest
    ),
    Route.MIN: RouteConfiguration(schema=minmax_schema, request_class=MinMaxRequest),
    Route.MAX: RouteConfiguration(schema=minmax_schema, request_class=MinMaxRequest),
}
