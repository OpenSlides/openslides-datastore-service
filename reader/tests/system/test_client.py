from reader.flask_frontend.routes import Route
from shared.flask_frontend import ERROR_CODES
from shared.tests import assert_error_response


def test_no_json(client):
    response = client.post(Route.GET.URL, data="no_json")
    assert_error_response(response, ERROR_CODES.INVALID_REQUEST)


requests = [
    "str",
    [],
    42,
    {"invalid": "invalid"},
    {"fqid": 42},
    {"fqid": []},
    {"fqid": {}},
    {"fqid": "c/1", "mapped_fields": "field"},
    {"fqid": "c/1", "mapped_fields": 42},
    {"fqid": "c/1", "mapped_fields": {}},
    {"fqid": "c/1", "position": "str"},
    {"fqid": "c/1", "position": []},
    {"fqid": "c/1", "position": {}},
    {"fqid": "c/1", "get_deleted_models": 5},
    {"fqid": "c/1", "get_deleted_models": "str"},
    {"fqid": "c/1", "get_deleted_models": []},
    {"fqid": "c/1", "get_deleted_models": {}},
]


def test_invalid_requests(json_client):
    for request in requests:
        response = json_client.post(Route.GET.URL, request)
        assert_error_response(response, ERROR_CODES.INVALID_REQUEST)
