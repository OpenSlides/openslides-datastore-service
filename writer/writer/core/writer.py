from typing import List, Protocol, Union

from .write_request import WriteRequest


class Writer(Protocol):
    """ For detailed interface descriptions, see the docs repo. """

    def write(
        self,
        write_requests: Union[WriteRequest, List[WriteRequest]],
        log_all_modified_fields: bool = True,
    ) -> None:
        """ Writes into the DB. """

    def reserve_ids(self, collection: str, amount: int) -> List[int]:
        """ Gets multiple reserved ids """

    def truncate_db(self) -> None:
        """ Truncate all tables. Dev mode only """
