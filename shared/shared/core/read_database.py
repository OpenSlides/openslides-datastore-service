from typing import Any, Dict, List, Protocol

from shared.di import service_interface


@service_interface
class ReadDatabase(Protocol):
    def get_models(self, fqids: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        Returns all requested models in a lookup-able fashion mapped the
        fqid <-> model from the read-DB. If a fqid could not be found, the
        model is not included in the result.
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
