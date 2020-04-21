import pytest
from unittest.mock import MagicMock, patch
from reader.flask_frontend import FlaskFrontend
from reader.flask_frontend.routes import Route
from reader.flask_frontend.routes_handler import get_route, register_routes
from shared.flask_frontend import ERROR_CODES, InvalidRequest


def test_register_routes():
    app = MagicMock()

    register_routes(app, "prefix")

    # `call` objects are tuples in the fashion of (args, kwargs)
    routes = [call[0][1] for call in app.add_url_rule.call_args_list]
    assert routes == list(Route)
