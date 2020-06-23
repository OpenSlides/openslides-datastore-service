from dataclasses import dataclass
from typing import Any, Dict, List, TypedDict, cast

import fastjsonschema

from shared.di import injector
from shared.flask_frontend import InvalidRequest
from shared.typing import JSON, Collection
from shared.util import BadCodingError, SelfValidatingDataclass
from writer.core import (
    BaseRequestEvent,
    RequestCreateEvent,
    RequestDeleteEvent,
    RequestRestoreEvent,
    RequestUpdateEvent,
    Writer,
    WriteRequest,
)


write_schema = fastjsonschema.compile(
    {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "properties": {
            "user_id": {"type": "integer"},
            "information": {},
            "locked_fields": {
                "type": "object",
                "additionalProperties": {"type": "integer"},
            },
            "events": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "type": {
                            "type": "string",
                            "enum": ["create", "update", "delete", "restore"],
                        },
                        "fqid": {"type": "string"},
                    },
                    "required": ["type", "fqid"],
                },
            },
        },
        "required": ["user_id", "information", "locked_fields", "events"],
    }
)


class WriteRequestJSON(TypedDict):
    user_id: int
    information: JSON
    locked_fields: Dict[str, int]
    events: List[Dict[str, Any]]


class WriteHandler:
    def write(self, data: JSON) -> None:
        write_request = self.build_write_request(data)
        writer = injector.get(Writer)
        writer.write(write_request)

    def build_write_request(self, data: JSON) -> WriteRequest:
        try:
            parsed_data = cast(WriteRequestJSON, write_schema(data))
        except fastjsonschema.JsonSchemaException as e:
            raise InvalidRequest(e.message)

        user_id = parsed_data["user_id"]
        information = parsed_data["information"]
        locked_fields = parsed_data["locked_fields"]
        events = self.parse_events(parsed_data["events"])

        return WriteRequest(events, information, user_id, locked_fields)

    def parse_events(self, events: List[Dict[str, Any]]) -> List[BaseRequestEvent]:
        request_events = []
        for event in events:
            type = event["type"]

            if type in ("create", "update"):
                fields = event.get("fields")
                if not isinstance(fields, dict):
                    raise InvalidRequest("Fields must be a dict")
                for key, value in fields.items():
                    if not isinstance(key, str):
                        raise InvalidRequest("Each key of fields must be a string")
            request_events.append(self.create_event(event))
        return request_events

    def create_event(self, event: Dict[str, Any]) -> BaseRequestEvent:
        type = event["type"]
        fqid = event["fqid"]
        request_event: BaseRequestEvent
        if type == "create":
            request_event = RequestCreateEvent(fqid, event["fields"])
        elif type == "update":
            request_event = RequestUpdateEvent(fqid, event["fields"])
        elif type == "delete":
            request_event = RequestDeleteEvent(fqid)
        elif type == "restore":
            request_event = RequestRestoreEvent(fqid)
        else:
            raise BadCodingError()
        return request_event


reserve_ids_schema = fastjsonschema.compile(
    {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "properties": {
            "amount": {"type": "integer"},
            "collection": {"type": "string"},
        },
        "required": ["amount", "collection"],
    }
)


@dataclass
class ReserveIdsRequestJSON(SelfValidatingDataclass):
    collection: Collection
    amount: int


class ReserveIdsHandler:
    def reserve_ids(self, data: JSON) -> List[int]:
        try:
            parsed_data = ReserveIdsRequestJSON(**reserve_ids_schema(data))
        except fastjsonschema.JsonSchemaException as e:
            raise InvalidRequest(e.message)

        writer = injector.get(Writer)
        return writer.reserve_ids(parsed_data.collection, parsed_data.amount)
