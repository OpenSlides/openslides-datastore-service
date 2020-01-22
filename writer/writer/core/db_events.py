from typing import Dict, List

from writer.shared import META_DELETED
from writer.shared.typing import JSON


class BaseDbEvent:
    def __init__(self, fqid: str) -> None:
        self.fqid = fqid

    def get_modified_fields(self) -> List[str]:
        raise NotImplementedError()


class DbCreateEvent(BaseDbEvent):
    def __init__(self, fqid: str, field_data: Dict[str, JSON]) -> None:
        super().__init__(fqid)
        self.field_data = field_data
        self.field_data[META_DELETED] = False

    def get_fields(self) -> List[str]:
        return list(self.field_data.keys())

    def get_modified_fields(self) -> List[str]:
        return self.get_fields()


class DbUpdateEvent(BaseDbEvent):
    def __init__(self, fqid: str, field_data: Dict[str, JSON]) -> None:
        super().__init__(fqid)
        self.field_data = field_data

    def get_fields(self) -> List[str]:
        return list(self.field_data.keys())

    def get_modified_fields(self) -> List[str]:
        return self.get_fields()


class DbDeleteFieldsEvent(BaseDbEvent):
    def __init__(self, fqid: str, fields: List[str]) -> None:
        super().__init__(fqid)
        self.fields = fields

    def get_modified_fields(self) -> List[str]:
        return self.fields


class DbDeleteEvent(BaseDbEvent):
    def set_modified_fields(self, fields: List[str]) -> None:
        self.modified_fields = fields

    def get_modified_fields(self) -> List[str]:
        return self.modified_fields


class DbRestoreEvent(BaseDbEvent):
    def set_modified_fields(self, fields: List[str]) -> None:
        self.modified_fields = fields

    def get_modified_fields(self) -> List[str]:
        return self.modified_fields
