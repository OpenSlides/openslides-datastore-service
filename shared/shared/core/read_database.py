from enum import Enum
from typing import Any, ContextManager, Dict, List, Protocol

from shared.di import service_interface


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

    def get_models(self, fqids: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        Returns all requested models in a lookup-able fashion mapped the
        fqid <-> model from the read-DB. If a fqid could not be found, the
        model is not included in the result.
        """

    def get_models_filtered(
        self, fqids: List[str], get_deleted_models: DeletedModelsBehaviour
    ) -> Dict[str, Dict[str, Any]]:
        """
        Same as get_models, but optionally filters by status.
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

    def build_model_ignore_deleted(self, fqid: str) -> Dict[str, Any]:
        """
        Rebuilds a deleted model, so it can be inserted into the read-db
        after a restore. It does not append META_POSITION to the model.
        """
