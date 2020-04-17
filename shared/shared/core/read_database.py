from enum import Enum
from typing import Any, ContextManager, Dict, List, Optional, Protocol, Tuple

from shared.core import Filter
from shared.di import service_interface
from shared.util import Model


class DeletedModelsBehaviour(int, Enum):
    NO_DELETED = 1
    ONLY_DELETED = 2
    ALL_MODELS = 3


@service_interface
class ReadDatabase(Protocol):
    def get_context(self) -> ContextManager[None]:
        """
        Creates a new context to execute all actions inside
        """

    def get(self, fqid: str, mapped_fields: List[str] = []) -> Model:
        """
        Internally calls `get_many` to retrieve a single model. Raises a
        ModelDoesNotExist if the model does not exist.
        """

    def get_many(
        self,
        fqids: List[str],
        mapped_fields_per_collection: Dict[str, List[str]] = {},
        get_deleted_models: DeletedModelsBehaviour = DeletedModelsBehaviour.ALL_MODELS,
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
    ) -> List[Model]:
        """
        Returns all models of the given collection. WARNING: May result in a huge
        amount of data. Use with caution!
        """

    def filter(
        self, collection: str, filter: Filter, mapped_fields: List[str]
    ) -> List[Model]:
        """
        Returns all models of the given collection that satisfy the filter criteria.
        May result in a huge amount of data when used with wide filters.
        """

    def aggregate(
        self,
        collection: str,
        filter: Filter,
        fields_params: Tuple[str, Optional[str], Optional[str]],
    ) -> Any:
        """
        Aggregates the filtered models according to fields_params.
        fields_params[0] must be one of `VALID_AGGREGATE_FUNCTIONS`.
        If fields_params[0] == "count", the optional parameters must be None-like
        and the amount of results is returned.
        Else fields_params[1] defines the field over which the aggregate is run and
        fields_params[2] defines the type to which the field is cast (must be one of
        `VALID_AGGREGATE_CAST_TARGETS`).
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
