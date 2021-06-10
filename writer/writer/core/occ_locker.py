from typing import Protocol

from shared.di import service_interface

from .write_request import WriteRequest


@service_interface
class OccLocker(Protocol):
    def assert_locked_fields(self, write_request: WriteRequest) -> None:
        """Raises ModelLocked if a position of at least one locked field is too old"""
