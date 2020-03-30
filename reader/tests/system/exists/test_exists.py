import json

from reader.flask_frontend.routes import Route
from shared.flask_frontend import ERROR_CODES
from shared.tests import assert_error_response
from shared.tests.util import assert_success_response


data = {
    "a/1": {
        "fqid": "a/1",
        "field_1": "data",
        "field_2": 42,
        "field_3": [1, 2, 3],
        "meta_position": 1,
    },
    "a/2": {
        "fqid": "a/2",
        "field_1": "test",
        "field_2": 42,
        "field_3": [1, 2, 3],
        "meta_position": 2,
    },
}
other_models = {
    "b/1": {
        "fqid": "b/1",
        "field_4": "data",
        "field_5": 42,
        "field_6": [1, 2, 3],
        "meta_position": 3,
    }
}


def setup_data(connection, cursor, deleted=False):
    for fqid, model in list(data.items()) + list(other_models.items()):
        cursor.execute("insert into models values (%s, %s)", [fqid, json.dumps(model)])
        cursor.execute("insert into models_lookup values (%s, %s)", [fqid, deleted])
    connection.commit()


def test_true(json_client, db_connection, db_cur):
    setup_data(db_connection, db_cur)
    response = json_client.post(
        Route.EXISTS.URL,
        {
            "collection": "a",
            "filter": {"field": "field_1", "operator": "=", "value": "data"},
        },
    )
    assert_success_response(response)
    assert response.json["exists"] is True


def test_false(json_client, db_connection, db_cur):
    setup_data(db_connection, db_cur)
    response = json_client.post(
        Route.EXISTS.URL,
        {
            "collection": "a",
            "filter": {"field": "field_1", "operator": "=", "value": "doesnt_exist"},
        },
    )
    assert_success_response(response)
    assert response.json["exists"] is False


def test_invalid_collection(json_client):
    response = json_client.post(
        Route.EXISTS.URL,
        {
            "collection": "not valid",
            "filter": {"field": "field", "operator": "=", "value": "data"},
        },
    )
    assert_error_response(response, ERROR_CODES.INVALID_FORMAT)


def test_invalid_field(json_client):
    response = json_client.post(
        Route.EXISTS.URL,
        {
            "collection": "a",
            "filter": {"field": "not valid", "operator": "=", "value": "data"},
        },
    )
    assert_error_response(response, ERROR_CODES.INVALID_FORMAT)


def test_invalid_operator(json_client):
    response = json_client.post(
        Route.EXISTS.URL,
        {
            "collection": "a",
            "filter": {"field": "field", "operator": "invalid", "value": "data"},
        },
    )
    assert_error_response(response, ERROR_CODES.INVALID_REQUEST)
