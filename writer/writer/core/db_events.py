from typing import Dict, List

from shared.typing import JSON
from shared.util import META_DELETED


class BaseDbEvent:
    def __init__(self, fqid: str) -> None:
        self.fqid = fqid

    def get_modified_fields(self) -> Dict[str, JSON]:
        raise NotImplementedError()


class BaseDbEventWithValues(BaseDbEvent):
    def __init__(self, fqid: str, field_data: Dict[str, JSON]) -> None:
        super().__init__(fqid)
        self.field_data = field_data

    def get_modified_fields(self) -> Dict[str, JSON]:
        return self.field_data


class BaseDbEventWithoutValues(BaseDbEvent):
    def set_modified_fields(self, fields: List[str]) -> None:
        self.fields = fields

    def get_modified_fields(self) -> Dict[str, JSON]:
        return {field: None for field in self.fields}


class DbCreateEvent(BaseDbEventWithValues):
    def __init__(self, fqid: str, field_data: Dict[str, JSON]) -> None:
        super().__init__(fqid, field_data)
        self.field_data[META_DELETED] = False


class DbUpdateEvent(BaseDbEventWithValues):
    pass


class DbDeleteFieldsEvent(BaseDbEventWithoutValues):
    def __init__(self, fqid: str, fields: List[str]) -> None:
        super().__init__(fqid)
        self.fields = fields


class DbDeleteEvent(BaseDbEventWithoutValues):
    pass


class DbRestoreEvent(BaseDbEventWithoutValues):
    pass
