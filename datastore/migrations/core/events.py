import json
from typing import Any, Dict, List

from datastore.shared.postgresql_backend import EVENT_TYPES, ListUpdatesDict
from datastore.shared.typing import Field, Fqid, Model
from datastore.shared.util import (
    InvalidKeyFormat,
    assert_is_field,
    assert_is_fqid,
    is_reserved_field,
)


class BadEventException(Exception):
    pass


def assert_no_special_field(field: Any) -> None:
    if is_reserved_field(field):
        raise BadEventException(f"Field {field} is reserved")


class BaseEvent:
    type: str

    def __init__(self, fqid: Fqid, data: Any) -> None:
        self.fqid = fqid
        self.data = data
        try:
            self.check()
        except InvalidKeyFormat as e:
            raise BadEventException(e.msg)

    def check(self):
        assert_is_fqid(self.fqid)

    def get_data(self) -> Any:
        return self.data

    def clone(self) -> "BaseEvent":
        data_copy = json.loads(json.dumps(self.get_data()))
        return self.__class__(self.fqid, data_copy)


class _ModelEvent(BaseEvent):
    def __init__(self, fqid: Fqid, data: Model) -> None:
        super().__init__(fqid, data)

    def check(self):
        super().check()
        for field, value in self.data.items():
            assert_is_field(field)
            assert_no_special_field(field)
            if value is None:
                raise BadEventException(f"The value of {field} must not be None")


class CreateEvent(_ModelEvent):
    type = EVENT_TYPES.CREATE


class UpdateEvent(_ModelEvent):
    type = EVENT_TYPES.UPDATE


class DeleteFieldsEvent(BaseEvent):
    type = EVENT_TYPES.DELETE_FIELDS

    def __init__(self, fqid: Fqid, data: List[Field]) -> None:
        super().__init__(fqid, data)

    def check(self) -> None:
        super().check()
        for field in self.data:
            assert_is_field(field)
            assert_no_special_field(field)


class ListUpdateEvent(BaseEvent):
    type = EVENT_TYPES.LIST_FIELDS

    def __init__(self, fqid: Fqid, data: Dict[str, ListUpdatesDict]) -> None:
        self.add = data.pop("add", {})
        self.remove = data.pop("remove", {})
        super().__init__(fqid, data)

    def check(self) -> None:
        if self.data:
            raise BadEventException("Only add and remove is allowed")

        all_fields = set(self.add.keys()).union(set(self.remove.keys()))
        for field in all_fields:
            assert_is_field(field)
            assert_no_special_field(field)

    def get_data(self) -> Any:
        return {"add": self.add, "remove": self.remove}


class DeleteEvent(BaseEvent):
    type = EVENT_TYPES.DELETE

    def __init__(self, fqid: Fqid, data: Any = None) -> None:
        super().__init__(fqid, None)


class RestoreEvent(BaseEvent):
    type = EVENT_TYPES.RESTORE

    def __init__(self, fqid: Fqid, data: Any = None) -> None:
        super().__init__(fqid, None)


EVENT_TYPE_TRANSLATION = {
    EVENT_TYPES.CREATE: CreateEvent,
    EVENT_TYPES.UPDATE: UpdateEvent,
    EVENT_TYPES.DELETE_FIELDS: DeleteFieldsEvent,
    EVENT_TYPES.LIST_FIELDS: ListUpdateEvent,
    EVENT_TYPES.DELETE: DeleteEvent,
    EVENT_TYPES.RESTORE: RestoreEvent,
}


def to_event(row) -> BaseEvent:
    if row["type"] not in EVENT_TYPE_TRANSLATION:
        raise BadEventException(f"Type {row['type']} is unknown")
    return EVENT_TYPE_TRANSLATION[row["type"]](row["fqid"], row["data"])
