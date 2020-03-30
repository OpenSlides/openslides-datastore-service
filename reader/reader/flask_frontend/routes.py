from enum import Enum

from shared.flask_frontend import unify_urls


URL_PREFIX = "/internal/datastore/reader/"


class Route(str, Enum):
    GET = "get"
    GET_MANY = "get_many"
    GET_ALL = "get_all"
    FILTER = "filter"
    EXISTS = "exists"
    COUNT = "count"
    MIN = "min"
    MAX = "max"

    @property
    def URL(self):
        return unify_urls(URL_PREFIX, self.value)
