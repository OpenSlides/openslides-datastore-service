import json

from reader.flask_frontend.routes import Route
from shared.flask_frontend import ERROR_CODES
from shared.tests import assert_error_response
from shared.tests.util import assert_success_response


data = {
    "a/1": {"field_1": "d", "meta_position": 2},
    "a/2": {"field_1": "c", "meta_position": 3},
    "a/3": {"field_1": "b", "meta_position": 4},
    "b/1": {"field_1": "a", "meta_position": 5},
}


def setup_data(connection, cursor, deleted=False):
    for fqid, model in data.items():
        cursor.execute("insert into models values (%s, %s)", [fqid, json.dumps(model)])
        cursor.execute("insert into models_lookup values (%s, %s)", [fqid, deleted])
    connection.commit()


def test_simple(json_client, db_connection, db_cur):
    setup_data(db_connection, db_cur)
    response = json_client.post(
        Route.MAX.URL,
        {
            "collection": "a",
            "filter": {"field": "field_1", "operator": "!=", "value": "invalid"},
            "field": "meta_position",
        },
    )
    assert_success_response(response)
    assert response.json["max"] == 4


def test_with_type(json_client, db_connection, db_cur):
    setup_data(db_connection, db_cur)
    response = json_client.post(
        Route.MAX.URL,
        {
            "collection": "a",
            "filter": {"field": "meta_position", "operator": "<", "value": 4},
            "field": "meta_position",
            "type": "int",
        },
    )
    assert_success_response(response)
    assert response.json["max"] == 3


def test_invalid_collection(json_client):
    response = json_client.post(
        Route.MAX.URL,
        {
            "collection": "not valid",
            "filter": {"field": "field", "operator": "=", "value": "data"},
            "field": "field",
        },
    )
    assert_error_response(response, ERROR_CODES.INVALID_FORMAT)


def test_invalid_field(json_client):
    response = json_client.post(
        Route.MAX.URL,
        {
            "collection": "collection",
            "filter": {"field": "field", "operator": "=", "value": "data"},
            "field": "not valid",
        },
    )
    assert_error_response(response, ERROR_CODES.INVALID_FORMAT)


def test_invalid_filter_field(json_client):
    response = json_client.post(
        Route.MAX.URL,
        {
            "collection": "a",
            "filter": {"field": "not valid", "operator": "=", "value": "data"},
            "field": "field",
        },
    )
    assert_error_response(response, ERROR_CODES.INVALID_FORMAT)


def test_invalid_operator(json_client):
    response = json_client.post(
        Route.MAX.URL,
        {
            "collection": "a",
            "filter": {"field": "field", "operator": "invalid", "value": "data"},
            "field": "field",
        },
    )
    assert_error_response(response, ERROR_CODES.INVALID_REQUEST)
