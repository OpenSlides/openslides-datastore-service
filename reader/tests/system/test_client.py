from shared.flask_frontend import ERROR_CODES
from shared.tests import assert_error_response
from tests.system.util import GET_URL


def test_no_json(client):
    response = client.post(GET_URL, data="no_json")
    assert_error_response(response, ERROR_CODES.INVALID_REQUEST)
