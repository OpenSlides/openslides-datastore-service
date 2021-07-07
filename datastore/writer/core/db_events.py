from typing import Dict, List, Tuple, Union

from datastore.shared.typing import JSON, Model
from datastore.shared.util import META_DELETED, BadCodingError, InvalidFormat


ListUpdatesDict = Dict[str, List[Union[str, int]]]


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


class DbListUpdateEvent(BaseDbEvent):
    """
    Before get_modified_fields can be called, the list updates have to be translated
    first via the translate_events method. All list updates can be reduced to a list
    of normal update and delete_fields events which are saved in self.events and whose
    modified fields are returned in the aforementioned method.
    The translation is necessary since the current state of the field in the datastore
    influences the result of the list update.
    """

    def __init__(
        self, fqid: str, add: ListUpdatesDict, remove: ListUpdatesDict
    ) -> None:
        super().__init__(fqid)
        self.add = add
        self.remove = remove
        self.events: List[BaseDbEvent] = []

    def translate_events(self, model: Model) -> None:
        if self.events:
            raise BadCodingError()
        updated_fields, deleted_fields = self.calculate_updated_fields(model)
        if updated_fields:
            self.events.append(DbUpdateEvent(self.fqid, updated_fields))
        if deleted_fields:
            self.events.append(DbDeleteFieldsEvent(self.fqid, deleted_fields))
        if not self.events:
            raise BadCodingError()

    def get_translated_events(self) -> List[BaseDbEvent]:
        if not self.events:
            raise BadCodingError("Fields have to be translated first")
        return self.events

    def calculate_updated_fields(self, model: Model) -> Tuple[Model, List[str]]:
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

        updated_fields = {}
        deleted_fields = []
        for field, value in self.add.items():
            # Iterate over list and remove all entries from value which are already
            # in the list. If adding multiple entries, this reduces the runtime needed.
            # When a huge amount of data is added, the normal update should be used
            # instead.
            db_list = model.get(field, [])
            for el in db_list:
                if el in value:
                    value.remove(el)
            updated_fields[field] = db_list + value

        for field, value in self.remove.items():
            if field in model:
                if field in updated_fields:
                    db_list = updated_fields[field]
                else:
                    db_list = model.get(field)
                updated_list = [el for el in db_list if el not in value]
                updated_fields[field] = updated_list
            else:
                deleted_fields.append(field)

        return updated_fields, deleted_fields

    def get_modified_fields(self) -> Dict[str, JSON]:
        modified_fields = {}
        for event in self.get_translated_events():
            modified_fields.update(event.get_modified_fields())
        return modified_fields


class DbDeleteFieldsEvent(BaseDbEventWithoutValues):
    def __init__(self, fqid: str, fields: List[str]) -> None:
        super().__init__(fqid)
        self.fields = fields


class DbDeleteEvent(BaseDbEventWithoutValues):
    pass


class DbRestoreEvent(BaseDbEventWithoutValues):
    pass
