from unittest.mock import MagicMock

import pytest

from datastore.reader.core import Reader
from datastore.reader.core.requests import GetManyRequest, GetRequest
from datastore.reader.flask_frontend.json_handler import JSONHandler
from datastore.reader.flask_frontend.routes import (
    Route,
    RouteConfiguration,
    get_schema,
    route_configurations,
)
from datastore.shared.di import injector
from datastore.shared.flask_frontend import InvalidRequest
from datastore.shared.util import BadCodingError
from tests import reset_di  # noqa


@pytest.fixture(autouse=True)
def provide_di(reset_di):  # noqa
    injector.register_as_singleton(Reader, MagicMock)


@pytest.fixture()
def reader(provide_di):  # noqa
    yield injector.get(Reader)


def test_handle_request(reader):
    reader.get = get = MagicMock()

    json_handler = JSONHandler()
    json_handler.handle_request(Route.GET, {"fqid": "c/1"})

    request = get.call_args.args[0]
    assert isinstance(request, GetRequest)
    assert request.fqid == "c/1"


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

    route_configurations[Route.GET] = RouteConfiguration(
        schema=get_schema, request_class=GetManyRequest
    )

    with pytest.raises(BadCodingError):
        json_handler.handle_request(Route.GET, {"fqid": "c/1"})
