import json

from reader.flask_frontend.routes import Route
from shared.flask_frontend import ERROR_CODES
from shared.tests import assert_error_response
from shared.tests.util import assert_success_response
from shared.util import DeletedModelsBehaviour


data = {
    "b/1": {
        "field_4": "data",
        "field_5": 42,
        "field_6": [1, 2, 3],
        "meta_position": 2,
    },
    "b/2": {
        "field_4": "data",
        "field_5": 42,
        "field_6": [1, 2, 3],
        "meta_position": 3,
    },
}
other_models = {
    "a/2": {"field_1": "data", "field_2": 42, "field_3": [1, 2, 3], "meta_position": 1}
}


def setup_data(connection, cursor, deleted=999):
    for i, (fqid, model) in enumerate(list(data.items()) + list(other_models.items())):
        cursor.execute("insert into models values (%s, %s)", [fqid, json.dumps(model)])
        cursor.execute(
            "insert into models_lookup values (%s, %s)", [fqid, (i + 1) % deleted == 0]
        )
    connection.commit()


def test_simple(json_client, db_connection, db_cur):
    setup_data(db_connection, db_cur)
    response = json_client.post(Route.GET_ALL.URL, {"collection": "b"})
    assert_success_response(response)
    assert response.json == list(data.values())


def test_deleted(json_client, db_connection, db_cur):
    setup_data(db_connection, db_cur, 2)
    response = json_client.post(Route.GET_ALL.URL, {"collection": "b"})
    assert_success_response(response)
    assert response.json == [data["b/1"]]


def test_only_deleted(json_client, db_connection, db_cur):
    setup_data(db_connection, db_cur, 2)
    response = json_client.post(
        Route.GET_ALL.URL,
        {"collection": "b", "get_deleted_models": DeletedModelsBehaviour.ONLY_DELETED},
    )
    assert_success_response(response)
    assert response.json == [data["b/2"]]


def test_deleted_all_models(json_client, db_connection, db_cur):
    setup_data(db_connection, db_cur, 2)
    response = json_client.post(
        Route.GET_ALL.URL,
        {"collection": "b", "get_deleted_models": DeletedModelsBehaviour.ALL_MODELS},
    )
    assert_success_response(response)
    assert response.json == list(data.values())


def test_mapped_fields(json_client, db_connection, db_cur):
    setup_data(db_connection, db_cur)
    response = json_client.post(
        Route.GET_ALL.URL,
        {"collection": "b", "mapped_fields": ["field_4", "meta_position"]},
    )
    assert_success_response(response)
    assert response.json == [
        {"field_4": "data", "meta_position": 2},
        {"field_4": "data", "meta_position": 3},
    ]


def test_invalid_collection(json_client):
    response = json_client.post(Route.GET_ALL.URL, {"collection": "not valid"})
    assert_error_response(response, ERROR_CODES.INVALID_FORMAT)


def test_invalid_mapped_fields(json_client):
    response = json_client.post(
        Route.GET_ALL.URL, {"collection": "a", "mapped_fields": ["not valid"]}
    )
    assert_error_response(response, ERROR_CODES.INVALID_FORMAT)
