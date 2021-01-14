from dataclasses import dataclass
from typing import Dict, Protocol, Union

from shared.di import service_interface
from shared.util import Filter, SelfValidatingDataclass


@dataclass
class CollectionFieldLockWithFilter(SelfValidatingDataclass):
    position: int
    filter: Filter


CollectionFieldLock = Union[int, CollectionFieldLockWithFilter]


@service_interface
class OccLocker(Protocol):
    def assert_fqid_positions(self, fqids: Dict[str, int]) -> None:
        """ Raises ModelLocked if a position of at least one fqid is too old """

    def assert_fqfield_positions(self, fqfields: Dict[str, int]) -> None:
        """ Raises ModelLocked if a position of at least one fqfield is too old """

    def assert_collectionfield_positions(
        self, collectionfields: Dict[str, CollectionFieldLock]
    ) -> None:
        """
        Raises ModelLocked if a position of at least one
        collectionfield is too old
        """
