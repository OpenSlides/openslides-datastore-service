from reader.flask_frontend.routes import Route
from shared.flask_frontend import ERROR_CODES
from shared.tests import assert_error_response


def test_no_json(client):
    response = client.post(Route.GET.URL, data="no_json")
    assert_error_response(response, ERROR_CODES.INVALID_REQUEST)
