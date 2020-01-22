from typing import Dict, Protocol

from writer.di import service_interface


@service_interface
class OccLocker(Protocol):
    def assert_fqid_positions(self, fqids: Dict[str, int]) -> None:
        """ Raises ModelLocked if a position of at least one fqid is too old """

    def assert_fqfield_positions(self, fqfields: Dict[str, int]) -> None:
        """ Raises ModelLocked if a position of at least one fqfield is too old """

    def assert_collectionfield_positions(
        self, collectionfields: Dict[str, int]
    ) -> None:
        """
        Raises ModelLocked if a position of at least one
        collectionfield is too old
        """
