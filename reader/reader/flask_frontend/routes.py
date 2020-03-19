from enum import Enum


class Route(Enum):
    GET = "get"
    GET_MANY = "get_many"
    GET_ALL = "get_all"
    FILTER = "filter"
    EXISTS = "exists"
    COUNT = "count"
    MIN = "min"
    MAX = "max"
