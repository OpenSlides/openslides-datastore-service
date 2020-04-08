import pytest

from reader.core.requests import GetManyRequest
from reader.flask_frontend.json_handler import JSONHandler, get_schema, request_map
from reader.flask_frontend.routes import Route
from shared.flask_frontend import InvalidRequest
from shared.util import BadCodingError


def test_handle_request_invalid_route():
    json_handler = JSONHandler()

    with pytest.raises(BadCodingError):
        json_handler.handle_request("invalid", None)


def test_handle_request_invalid_data():
    json_handler = JSONHandler()

    with pytest.raises(InvalidRequest):
        json_handler.handle_request(Route.GET, "invalid")


def test_handle_request_invalid_config():
    json_handler = JSONHandler()

    request_map[Route.GET] = {
        "schema": get_schema,
        "request_class": GetManyRequest,
    }

    with pytest.raises(BadCodingError):
        json_handler.handle_request(Route.GET, {"fqid": "fqid"})
