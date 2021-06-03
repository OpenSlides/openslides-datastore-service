from dataclasses import dataclass
from typing import Any, ContextManager, Dict, List, Optional, Protocol

from shared.di import service_interface
from shared.typing import Model
from shared.util import DeletedModelsBehaviour, Filter


class BaseFilterQueryFieldsParameters:
    pass


@dataclass
class MappedFieldsFilterQueryFieldsParameters(BaseFilterQueryFieldsParameters):
    mapped_fields: List[str]


@dataclass
class BaseAggregateFilterQueryFieldsParameters(BaseFilterQueryFieldsParameters):
    function: str


@dataclass
class CountFilterQueryFieldsParameters(BaseAggregateFilterQueryFieldsParameters):
    function: str = "count"


@dataclass
class AggregateFilterQueryFieldsParameters(BaseAggregateFilterQueryFieldsParameters):
    function: str
    field: str
    type: str


@service_interface
class ReadDatabase(Protocol):
    def get_context(self) -> ContextManager[None]:
        """
        Creates a new context to execute all actions inside
        """

    def get(
        self,
        fqid: str,
        mapped_fields: List[str] = [],
        get_deleted_models: DeletedModelsBehaviour = DeletedModelsBehaviour.NO_DELETED,
    ) -> Model:
        """
        Internally calls `get_many` to retrieve a single model. Raises a
        ModelDoesNotExist if the model does not exist.
        """

    def get_many(
        self,
        fqids: List[str],
        mapped_fields_per_fqid: Dict[str, List[str]] = {},
        get_deleted_models: DeletedModelsBehaviour = DeletedModelsBehaviour.NO_DELETED,
    ) -> Dict[str, Model]:
        """
        Returns all requested models in a lookup-able fashion mapped the
        fqid <-> model from the read-DB. If a fqid could not be found, the
        model is not included in the result.
        """

    def get_all(
        self,
        collection: str,
        mapped_fields: List[str],
        get_deleted_models: DeletedModelsBehaviour = DeletedModelsBehaviour.NO_DELETED,
    ) -> Dict[int, Model]:
        """
        Returns all models of the given collection. WARNING: May result in a huge
        amount of data. Use with caution!
        """

    def get_everything(
        self,
        get_deleted_models: DeletedModelsBehaviour = DeletedModelsBehaviour.NO_DELETED,
    ) -> Dict[str, List[Model]]:
        """
        Returns all models of the given collection. WARNING: May result in a huge
        amount of data. Use with caution!
        """

    def filter(
        self, collection: str, filter: Filter, mapped_fields: List[str]
    ) -> Dict[int, Model]:
        """
        Returns all models of the given collection that satisfy the filter criteria.
        May result in a huge amount of data when used with wide filters.
        """

    def aggregate(
        self,
        collection: str,
        filter: Filter,
        fields_params: BaseAggregateFilterQueryFieldsParameters,
    ) -> Any:
        """
        Aggregates the filtered models according to fields_params.
        """

    def create_or_update_models(self, models: Dict[str, Dict[str, Any]]) -> None:
        """
        Creates or updates models in the read-DB. The models are given
        in a map from fqid <-> model
        """

    def delete_models(self, fqids: List[str]) -> None:
        """
        Delete all given models from the read-DB
        """

    def build_model_ignore_deleted(
        self, fqid: str, position: Optional[int] = None
    ) -> Model:
        """
        Calls `build_models_ignore_deleted` to build a single model.
        Raises ModelDoesNotExist if the model does not exist.
        """

    def build_models_ignore_deleted(
        self, fqids: List[str], position: Optional[int] = None
    ) -> Dict[str, Model]:
        """
        Builds the given models, optionally only up to the given position.
        It does not append META_POSITION to the model.
        """

    def is_deleted(self, fqid: str, position: Optional[int] = None) -> bool:
        """
        Calls `get_deleted_status` to retrieve the deleted state of a single model.
        Raises ModelDoesNotExist if the model does not exist.
        """

    def get_deleted_status(
        self, fqids: List[str], position: Optional[int] = None
    ) -> Dict[str, bool]:
        """
        Returns a map indicating if the models with the given fqids are deleted. If
        position is given, the result refers to the state at the position.
        """

    def get_position(self) -> int:
        """Returns the current (highest) position of the datastore."""
