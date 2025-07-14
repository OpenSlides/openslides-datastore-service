from collections import defaultdict
from typing import Any, Callable, Dict, Iterable, List, Optional, Protocol

from datastore.reader.core import (
    AggregateRequest,
    FilterRequest,
    GetAllRequest,
    GetManyRequest,
    GetRequest,
    MinMaxRequest,
    Reader,
)
from datastore.reader.core.requests import GetManyRequestPart
from datastore.shared.di import service_as_factory, service_interface
from datastore.shared.postgresql_backend import filter_models
from datastore.shared.services.read_database import HistoryInformation, ReadDatabase
from datastore.shared.typing import Collection, Field, Fqid, Id, Model, Position
from datastore.shared.util import ModelDoesNotExist, collection_from_fqid
from datastore.shared.util.filter import Filter
from datastore.shared.util.key_transforms import fqid_from_collection_and_id


@service_interface
class MigrationReader(Protocol):
    """
    Adaption of the Reader protocol for ease of use in migrations. Provides access to all current
    models which are not deleted.
    """

    is_in_memory_migration: bool = False

    def get(self, fqid: Fqid, mapped_fields: List[Field] = []) -> Model: ...

    def get_many(
        self, requests: List[GetManyRequestPart]
    ) -> Dict[Collection, Dict[Id, Model]]: ...

    def get_all(
        self, collection: Collection, mapped_fields: List[Field] = []
    ) -> Dict[Id, Model]: ...

    def filter(
        self, collection: Collection, filter: Filter, mapped_fields: List[Field] = []
    ) -> Dict[Id, Model]: ...

    def exists(self, collection: Collection, filter: Filter) -> bool: ...

    def count(self, collection: Collection, filter: Filter) -> int: ...

    def min(
        self, collection: Collection, filter: Filter, field: Field
    ) -> Optional[int]: ...

    def max(
        self, collection: Collection, filter: Filter, field: Field
    ) -> Optional[int]: ...

    def is_alive(self, fqid: Fqid) -> bool:
        """Returns true iff the model exists and is not deleted."""

    def is_deleted(self, fqid: Fqid) -> bool:
        """Returns true iff the model exists and is deleted."""

    def model_exists(self, fqid: Fqid) -> bool:
        """Returns true iff the model exists, regardless of deletion status."""

    def get_max_position(self) -> Position: ...

    def get_history_positions(
        self, from_position: int = 0, to_position: int | None = None
    ) -> tuple[List[HistoryInformation], dict[int, list[str]]]: ...


@service_as_factory
class MigrationReaderImplementation(MigrationReader):
    reader: Reader
    read_database: ReadDatabase

    def get(self, fqid: Fqid, mapped_fields: List[Field] = []) -> Model:
        return self.reader.get(GetRequest(fqid, mapped_fields))

    def get_many(
        self, requests: List[GetManyRequestPart]
    ) -> Dict[Collection, Dict[Id, Model]]:
        return self.reader.get_many(GetManyRequest(requests))

    def get_all(
        self, collection: Collection, mapped_fields: List[Field] = []
    ) -> Dict[Id, Model]:
        return self.reader.get_all(GetAllRequest(collection, mapped_fields))

    def filter(
        self, collection: Collection, filter: Filter, mapped_fields: List[Field] = []
    ) -> Dict[Id, Model]:
        result = self.reader.filter(FilterRequest(collection, filter, mapped_fields))
        return result["data"]

    def exists(self, collection: Collection, filter: Filter) -> bool:
        result = self.reader.exists(AggregateRequest(collection, filter))
        return result["exists"]

    def count(self, collection: Collection, filter: Filter) -> int:
        result = self.reader.count(AggregateRequest(collection, filter))
        return result["count"]

    def min(
        self, collection: Collection, filter: Filter, field: Field
    ) -> Optional[int]:
        result = self.reader.min(MinMaxRequest(collection, filter, field))
        return result["min"]

    def max(
        self, collection: Collection, filter: Filter, field: Field
    ) -> Optional[int]:
        result = self.reader.max(MinMaxRequest(collection, filter, field))
        return result["max"]

    def is_alive(self, fqid: Fqid) -> bool:
        status = self.read_database.get_deleted_status([fqid])
        return status.get(fqid) is False

    def is_deleted(self, fqid: Fqid) -> bool:
        status = self.read_database.get_deleted_status([fqid])
        return status.get(fqid) is True

    def model_exists(self, fqid: Fqid) -> bool:
        status = self.read_database.get_deleted_status([fqid])
        return fqid in status

    def get_max_position(self) -> Position:
        return self.read_database.get_max_position()

    def get_history_positions(
        self, from_position: int = 0, to_position: int | None = None
    ) -> tuple[List[HistoryInformation], dict[int, list[str]]]:
        return self.read_database.get_history_positions(from_position, to_position)


@service_as_factory
class MigrationReaderImplementationMemory(MigrationReader):
    """
    In-memory implementation of the read database. All `mapped_fields` are ignored, all fields are
    always returned.
    """

    models: Dict[Fqid, Model]
    is_in_memory_migration: bool = True

    def get(self, fqid: Fqid, mapped_fields: List[Field] = []) -> Model:
        return self._get_deep_copy_by_fqid(fqid, mapped_fields)

    def get_many(
        self, requests: List[GetManyRequestPart]
    ) -> Dict[Collection, Dict[Id, Model]]:
        result: Dict[Collection, Dict[Id, Model]] = defaultdict(dict)
        for request in requests:
            for id in request.ids:
                fqid = fqid_from_collection_and_id(request.collection, id)
                if fqid in self.models:
                    result[request.collection][id] = self._deep_copy_dict(
                        self.models[fqid], request.mapped_fields
                    )
        return result

    def get_all(
        self, collection: Collection, mapped_fields: List[Field] = []
    ) -> Dict[Id, Model]:
        return {
            model["id"]: self._deep_copy_dict(model, mapped_fields)
            for fqid, model in self.models.items()
            if collection_from_fqid(fqid) == collection
        }

    def filter(
        self, collection: Collection, filter: Filter, mapped_fields: List[Field] = []
    ) -> Dict[Id, Model]:
        return filter_models(self.models, collection, filter, mapped_fields)

    def exists(self, collection: Collection, filter: Filter) -> bool:
        return self.count(collection, filter) > 0

    def count(self, collection: Collection, filter: Filter) -> int:
        return len(self.filter(collection, filter))

    def min(
        self, collection: Collection, filter: Filter, field: Field
    ) -> Optional[int]:
        return self.minmax(collection, filter, field, min)

    def max(
        self, collection: Collection, filter: Filter, field: Field
    ) -> Optional[int]:
        return self.minmax(collection, filter, field, max)

    def minmax(
        self,
        collection: Collection,
        filter: Filter,
        field: Field,
        func: Callable[[Iterable[int]], int],
    ) -> Optional[int]:
        values = [
            model[field]
            for model in self.filter(collection, filter).values()
            if field in model
        ]
        if values:
            return func(values)
        return None

    def is_alive(self, fqid: Fqid) -> bool:
        # the in-memory implementation does not support deletion
        return self.model_exists(fqid)

    def is_deleted(self, fqid: Fqid) -> bool:
        # the in-memory implementation does not support deletion
        return False

    def model_exists(self, fqid: Fqid) -> bool:
        return fqid in self.models

    def _get_deep_copy_by_fqid(
        self, fqid: str, mapped_fields: List[Field]
    ) -> dict[str, Any]:
        """
        Creates a deep copy of given model fqid recursively. Assumes no circular references between dict and subdicts.
        Also filters all non mapped fields out.
        """
        if fqid not in self.models:
            raise ModelDoesNotExist(fqid)
        return self._deep_copy_dict(self.models[fqid], mapped_fields)

    def _deep_copy_dict(
        self, model: dict[str, Any], mapped_fields: List[Field] = []
    ) -> dict[str, Any]:
        """
        Creates a deep copy of given dict recursively. Assumes no circular references between dict and subdicts.
        Also filters all non mapped fields out.
        """
        new_model: dict[str, Any] = dict()
        for key, value in model.items():
            if not mapped_fields or key in mapped_fields:
                if isinstance(value, dict):
                    new_model[key] = self._deep_copy_dict(model[key])
                elif isinstance(value, list):
                    new_model[key] = value.copy()
                else:
                    new_model[key] = value
        return new_model

    def get_max_position(self) -> Position:
        return -1

    def get_history_positions(
        self, from_position: int = 0, to_position: int | None = None
    ) -> tuple[List[HistoryInformation], dict[int, list[str]]]:
        return [], {}
