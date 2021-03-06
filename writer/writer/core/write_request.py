from typing import Any, Dict, List, TypedDict, Union, cast

from dacite import from_dict
from dacite.exceptions import MissingValueError, UnionMatchError

from shared.flask_frontend import InvalidRequest
from shared.typing import JSON
from shared.util import (
    KEY_TYPE,
    BadCodingError,
    InvalidFormat,
    assert_is_field,
    assert_is_fqid,
    get_key_type,
    is_reserved_field,
)

from . import CollectionFieldLock, CollectionFieldLockWithFilter
from .db_events import ListUpdatesDict


ListFieldsData = TypedDict(
    "ListFieldsData",
    {"add": ListUpdatesDict, "remove": ListUpdatesDict},
    total=False,
)


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
    def __init__(
        self, fqid: str, fields: Dict[str, JSON], list_fields: ListFieldsData = {}
    ) -> None:
        super().__init__(fqid)
        add_list_fields = list_fields.get("add", {})
        remove_list_fields = list_fields.get("remove", {})

        fields_keys = set(fields.keys())
        add_list_fields_keys = set(add_list_fields.keys())
        remove_list_fields_keys = set(remove_list_fields.keys())

        all_keys = fields_keys.union(add_list_fields_keys, remove_list_fields_keys)
        if len(all_keys) == 0:
            raise InvalidRequest("No fields are given")
        if len(all_keys) < len(fields) + len(add_list_fields) + len(remove_list_fields):
            raise InvalidRequest("You cannot give a field name multiple times")
        for field in all_keys:
            assert_is_field(field)
            assert_no_special_field(field)
        self.fields = fields
        self.list_fields = list_fields


class RequestDeleteEvent(BaseRequestEvent):
    pass


class RequestRestoreEvent(BaseRequestEvent):
    pass


LockedFieldsJSON = Union[int, Dict[str, Any]]


class WriteRequest:
    def __init__(
        self,
        events: List[BaseRequestEvent],
        information: JSON,
        user_id: int,
        locked_fields: Dict[str, LockedFieldsJSON],
    ) -> None:
        self.events = events
        self.information = information
        self.user_id = user_id
        if len(events) <= 0:
            raise InvalidFormat("No events were given")
        self.parse_locked_fields(locked_fields)

    def parse_locked_fields(self, locked_fields: Dict[str, LockedFieldsJSON]) -> None:
        self.locked_fqids: Dict[str, int] = {}
        self.locked_fqfields: Dict[str, int] = {}
        self.locked_collectionfields: Dict[str, CollectionFieldLock] = {}
        for key, position in locked_fields.items():
            self.handle_single_key(key, position)

    def handle_single_key(self, key: str, cf_lock: LockedFieldsJSON) -> None:
        if isinstance(cf_lock, int) and cf_lock <= 0:
            raise InvalidFormat(f"The position of key {key} must be >= 0")

        key_type = get_key_type(key)
        if key_type in (KEY_TYPE.FQID, KEY_TYPE.FQFIELD) and not isinstance(
            cf_lock, int
        ):
            raise InvalidFormat(
                "CollectionFieldLocks can only be used with collectionfields"
            )

        if key_type == KEY_TYPE.FQID:
            self.locked_fqids[key] = cast(int, cf_lock)
        elif key_type == KEY_TYPE.FQFIELD:
            self.locked_fqfields[key] = cast(int, cf_lock)
        elif key_type == KEY_TYPE.COLLECTIONFIELD:
            if isinstance(cf_lock, int):
                self.locked_collectionfields[key] = cf_lock
            else:
                # build self validating data class
                try:
                    self.locked_collectionfields[key] = from_dict(
                        CollectionFieldLockWithFilter,
                        cf_lock,
                    )
                except (TypeError, MissingValueError, UnionMatchError) as e:
                    raise BadCodingError("Invalid data to initialize class\n" + str(e))
