from typing import Any, Dict, List

from writer.shared import is_reserved_field
from writer.shared.typing import JSON

from .exceptions import InvalidFormat
from .key_types import KEY_TYPE, assert_is_field, assert_is_fqid, get_key_type


def assert_no_special_field(field: Any) -> None:
    if is_reserved_field(field):
        raise InvalidFormat(f"Field {field} is reserved")


class BaseRequestEvent:
    def __init__(self, fqid: str) -> None:
        assert_is_fqid(fqid)
        self.fqid = fqid


class RequestCreateEvent(BaseRequestEvent):
    def __init__(self, fqid: str, fields: Dict[str, JSON]) -> None:
        super().__init__(fqid)
        self.prune_empty_values(fields)
        for field in fields.keys():
            assert_is_field(field)
            assert_no_special_field(field)
        self.fields = fields

    def prune_empty_values(self, fields):
        for key, value in list(fields.items()):
            if value is None:
                del fields[key]


class RequestUpdateEvent(BaseRequestEvent):
    def __init__(self, fqid: str, fields: Dict[str, JSON]) -> None:
        super().__init__(fqid)
        if len(fields) <= 0:
            raise InvalidFormat("No fields are given")
        for field in fields.keys():
            assert_is_field(field)
            assert_no_special_field(field)
            self.fields = fields


class RequestDeleteEvent(BaseRequestEvent):
    pass


class RequestRestoreEvent(BaseRequestEvent):
    pass


class WriteRequest:
    def __init__(
        self,
        events: List[BaseRequestEvent],
        information: JSON,
        user_id: int,
        locked_fields: Dict[str, int],
    ) -> None:
        self.events = events
        self.information = information
        self.user_id = user_id
        if len(events) <= 0:
            raise InvalidFormat("No events were given")
        self.parse_locked_fields(locked_fields)

    def parse_locked_fields(self, locked_fields: Dict[str, int]) -> None:
        self.locked_fqids: Dict[str, int] = {}
        self.locked_fqfields: Dict[str, int] = {}
        self.locked_collectionfields: Dict[str, int] = {}
        for key, position in locked_fields.items():
            self.handle_single_key(key, position)

    def handle_single_key(self, key: str, position: int) -> None:
        if position <= 0:
            raise InvalidFormat(f"The position of key {key} must be >= 0")

        key_type = get_key_type(key)
        if key_type == KEY_TYPE.FQID:
            self.locked_fqids[key] = position
        elif key_type == KEY_TYPE.FQFIELD:
            self.locked_fqfields[key] = position
        elif key_type == KEY_TYPE.COLLECTIONFIELD:
            self.locked_collectionfields[key] = position
