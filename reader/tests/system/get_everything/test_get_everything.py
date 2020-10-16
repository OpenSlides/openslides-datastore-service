import json

from reader.flask_frontend.routes import Route
from shared.tests.util import assert_success_response
from shared.util import DeletedModelsBehaviour, id_from_fqid


data = {
    "a/1": {
        "field_4": "data",
        "field_5": 42,
        "field_6": [1, 2, 3],
        "meta_position": 2,
    },
    "a/2": {
        "field_4": "data",
        "field_5": 42,
        "field_6": [1, 2, 3],
        "meta_position": 2,
    },
    "b/1": {
        "field_4": "data",
        "field_5": 42,
        "field_6": [1, 2, 3],
        "meta_position": 3,
    },
}


def setup_data(connection, cursor):
    # a/2 is deleted
    for fqid, model in data.items():
        cursor.execute("insert into models values (%s, %s)", [fqid, json.dumps(model)])
        cursor.execute(
            "insert into models_lookup values (%s, %s)", [fqid, fqid == "a/2"]
        )
    connection.commit()


def get_data_with_id(fqid):
    model = data[fqid]
    model["id"] = id_from_fqid(fqid)
    return model


def test_simple(json_client, db_connection, db_cur):
    setup_data(db_connection, db_cur)
    response = json_client.post(Route.GET_EVERYTHING.URL, {})
    assert_success_response(response)
    assert response.json == {
        "a": [get_data_with_id("a/1")],
        "b": [get_data_with_id("b/1")],
    }


def test_only_deleted(json_client, db_connection, db_cur):
    setup_data(db_connection, db_cur)
    response = json_client.post(
        Route.GET_EVERYTHING.URL,
        {"get_deleted_models": DeletedModelsBehaviour.ONLY_DELETED},
    )
    assert_success_response(response)
    assert response.json == {"a": [get_data_with_id("a/2")]}


def test_deleted_all_models(json_client, db_connection, db_cur):
    setup_data(db_connection, db_cur)
    response = json_client.post(
        Route.GET_EVERYTHING.URL,
        {"get_deleted_models": DeletedModelsBehaviour.ALL_MODELS},
    )
    assert_success_response(response)
    assert response.json == {
        "a": [get_data_with_id("a/1"), get_data_with_id("a/2")],
        "b": [get_data_with_id("b/1")],
    }
