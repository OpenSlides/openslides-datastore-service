from typing import Callable, Dict, Type, TypedDict

import fastjsonschema
from dacite import Config, from_dict
from dacite.exceptions import MissingValueError

from reader.core import Reader
from reader.core.requests import (
    AggregateRequest,
    FilterRequest,
    GetAllRequest,
    GetEverythingRequest,
    GetManyRequest,
    GetRequest,
    MinMaxRequest,
)
from shared.di import injector
from shared.flask_frontend import InvalidRequest
from shared.postgresql_backend.sql_query_helper import VALID_AGGREGATE_CAST_TARGETS
from shared.typing import JSON
from shared.util import BadCodingError, DeletedModelsBehaviour

from .routes import Route


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


class RequestMapEntry(TypedDict):
    schema: Callable
    request_class: Type


# maps all available routes to the respective schema
request_map: Dict[Route, RequestMapEntry] = {
    Route.GET: {"schema": get_schema, "request_class": GetRequest},
    Route.GET_MANY: {"schema": get_many_schema, "request_class": GetManyRequest},
    Route.GET_ALL: {"schema": get_all_schema, "request_class": GetAllRequest},
    Route.GET_EVERYTHING: {
        "schema": get_everything_schema,
        "request_class": GetEverythingRequest,
    },
    Route.FILTER: {"schema": filter_schema, "request_class": FilterRequest},
    Route.EXISTS: {"schema": aggregate_schema, "request_class": AggregateRequest},
    Route.COUNT: {"schema": aggregate_schema, "request_class": AggregateRequest},
    Route.MIN: {"schema": minmax_schema, "request_class": MinMaxRequest},
    Route.MAX: {"schema": minmax_schema, "request_class": MinMaxRequest},
}


class JSONHandler:
    def handle_request(self, route: Route, data: JSON) -> Dict:
        """
        A generic handler for all requests. Parses the request to a python object
        according to the request_map and execute the according function.
        """

        try:
            route_metadata = request_map[route]
            schema = route_metadata["schema"]
            request_class = route_metadata["request_class"]
        except KeyError:
            raise BadCodingError("Invalid route metadata: " + route)

        try:
            request_data = schema(data)
        except fastjsonschema.JsonSchemaException as e:
            raise InvalidRequest(e.message)

        try:
            request_object = from_dict(
                request_class, request_data, Config(check_types=False)
            )
        except (TypeError, MissingValueError) as e:
            raise BadCodingError("Invalid data to initialize class\n" + str(e))

        reader = injector.get(Reader)
        function = getattr(reader, route)
        return function(request_object)
