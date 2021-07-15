from typing import Protocol

from datastore.shared.di import service_as_singleton, service_interface


@service_interface
class MigrationLogger(Protocol):
    def set_verbose(self, verbose: bool) -> None:
        """
        Set, if verbose message should be logged.
        """

    def info(self, message: str) -> None:
        """
        Logs the message.
        """

    def debug(self, message: str) -> None:
        """
        Logs the message, if verbose is true.
        """


@service_as_singleton
class MigrationLoggerImplementation:
    def __init__(self):
        self.verbose: bool = False

    def set_verbose(self, verbose: bool) -> None:
        self.verbose = verbose

    def info(self, message: str) -> None:
        print(message)

    def debug(self, message: str) -> None:
        if self.verbose:
            print(message)
