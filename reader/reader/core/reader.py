from typing import List, Protocol, TypedDict

from .requests import (
    AggregateRequest,
    FilterRequest,
    GetAllRequest,
    GetManyRequest,
    GetRequest,
    MinMaxRequest,
)
from shared.util import Model


class ExistsResult(TypedDict):
    exists: bool
    position: int


class CountResult(TypedDict):
    count: bool
    position: int


class MinResult(TypedDict):
    min: bool
    position: int


class MaxResult(TypedDict):
    max: bool
    position: int


class Reader(Protocol):
    """ An abstract class for the reader. For more details, see the specs. """

    def get(self, request: GetRequest) -> Model:
        """ Gets the specified model. """

    def getMany(self, request: GetManyRequest) -> List[Model]:
        """ Gets multiple models. """

    def getAll(self, request: GetAllRequest) -> List[Model]:
        """
        Returns all (non-deleted) models of one collection. May return a huge amount
        of data, so use with caution.
        """

    def filter(self, request: FilterRequest) -> List[Model]:
        """ Returns all models that satisfy the filter condition. """

    def exists(self, request: AggregateRequest) -> ExistsResult:
        """ Determines whether at least one model satisfies the filter conditions. """

    def count(self, request: AggregateRequest) -> CountResult:
        """ Returns the amount of models taht satisfy the filter conditions. """

    def min(self, request: MinMaxRequest) -> MinResult:
        """
        Returns the mininum value of the given field for all models that satisfy the
        given filter.
        """

    def max(self, request: MinMaxRequest) -> MaxResult:
        """
        Returns the maximum value of the given field for all models that satisfy the
        given filter.
        """
