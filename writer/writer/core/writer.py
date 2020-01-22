from typing import List, Protocol

from .write_request import WriteRequest


class Writer(Protocol):
    """ For detailed interface descriptions, see the docs repo. """

    def write(self, write_request: WriteRequest) -> None:
        """ Writes into the DB. """

    def get_ids(self, collection: str, amount: int) -> List[int]:
        """ Gets multiple reserved ids """
