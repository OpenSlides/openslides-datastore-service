from typing import Dict, List

from datastore.shared.postgresql_backend import ListUpdatesDict, apply_fields
from datastore.shared.typing import JSON, Model
from datastore.shared.util import InvalidFormat


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
    def __init__(self, fqid: str, fields: List[str]) -> None:
        super().__init__(fqid)
        self.fields = fields

    def get_modified_fields(self) -> Dict[str, JSON]:
        return {field: None for field in self.fields}


class DbCreateEvent(BaseDbEventWithValues):
    pass


class DbUpdateEvent(BaseDbEventWithValues):
    pass


class DbListUpdateEvent(BaseDbEvent):
    def __init__(
        self, fqid: str, add: ListUpdatesDict, remove: ListUpdatesDict, model: Model
    ) -> None:
        super().__init__(fqid)
        self.add = add
        self.remove = remove

        self.modified_fields = self.calculate_modified_fields(model)

    def calculate_modified_fields(self, model: Model) -> Dict[str, JSON]:
        all_field_keys = list(self.add.keys()) + list(self.remove.keys())
        for field in all_field_keys:
            db_list = model.get(field, [])
            if not isinstance(db_list, list):
                raise InvalidFormat(
                    f"Field {field} on model {self.fqid} is not a list, but of type"
                    + str(type(db_list))
                )
            for el in db_list:
                if not isinstance(el, (str, int)):
                    raise InvalidFormat(
                        f"Field {field} on model {self.fqid} contains invalid entry "
                        f"for list update (of type {type(el)}): {el}"
                    )

        return apply_fields(model, self.add, self.remove)

    def get_modified_fields(self) -> Dict[str, JSON]:
        return self.modified_fields


class DbDeleteFieldsEvent(BaseDbEventWithoutValues):
    pass


class DbDeleteEvent(BaseDbEventWithoutValues):
    pass


class DbRestoreEvent(BaseDbEventWithoutValues):
    pass
