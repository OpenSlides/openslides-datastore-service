import json

from reader.flask_frontend.routes import Route
from shared.flask_frontend import ERROR_CODES
from shared.postgresql_backend import EVENT_TYPES
from shared.tests import assert_error_response
from shared.tests.util import assert_success_response
from shared.util import DeletedModelsBehaviour


data = {
    "a/1": {"field_1": "data", "field_2": 42, "field_3": [1, 2, 3], "common_field": 1},
    "b/1": {"field_4": "data", "field_5": 42, "field_6": [1, 2, 3], "common_field": 2},
    "b/2": {"field_4": "data", "field_5": 42, "field_6": [1, 2, 3], "common_field": 3},
}
default_request_parts = [
    {"collection": "a", "ids": [1]},
    {"collection": "b", "ids": [1, 2]},
]
default_request = {"requests": default_request_parts}


def setup_data(connection, cursor, deleted=False):
    for fqid, model in data.items():
        cursor.execute("insert into models values (%s, %s)", [fqid, json.dumps(model)])
        cursor.execute("insert into models_lookup values (%s, %s)", [fqid, deleted])
    connection.commit()


def test_simple(json_client, db_connection, db_cur):
    setup_data(db_connection, db_cur)
    response = json_client.post(Route.GET_MANY.URL, default_request)
    assert_success_response(response)
    assert response.json == data


def test_invalid_fqids(json_client, db_connection, db_cur):
    setup_data(db_connection, db_cur)
    request = {
        "requests": [
            {"collection": "a", "ids": [1]},
            {"collection": "b", "ids": [1, 2, 3]},
            {"collection": "c", "ids": [1]},
        ],
    }
    response = json_client.post(Route.GET_MANY.URL, request)
    assert_success_response(response)
    assert response.json == data


def test_only_invalid_fqids(json_client, db_connection, db_cur):
    setup_data(db_connection, db_cur)
    request = {
        "requests": [{"collection": "b", "ids": [3]}, {"collection": "c", "ids": [1]}],
    }
    response = json_client.post(Route.GET_MANY.URL, request)
    assert_success_response(response)
    assert response.json == {}


def test_no_deleted(json_client, db_connection, db_cur):
    setup_data(db_connection, db_cur, True)
    response = json_client.post(Route.GET_MANY.URL, default_request)
    assert_success_response(response)
    assert response.json == {}


def test_deleted(json_client, db_connection, db_cur):
    setup_data(db_connection, db_cur, True)
    request = {
        "requests": default_request_parts,
        "get_deleted_models": DeletedModelsBehaviour.ONLY_DELETED,
    }
    response = json_client.post(Route.GET_MANY.URL, request)
    assert_success_response(response)
    assert response.json == data


def test_deleted_not_deleted(json_client, db_connection, db_cur):
    setup_data(db_connection, db_cur)
    request = {
        "requests": default_request_parts,
        "get_deleted_models": DeletedModelsBehaviour.ONLY_DELETED,
    }
    response = json_client.post(Route.GET_MANY.URL, request)
    assert_success_response(response)
    assert response.json == {}


def test_mapped_fields(json_client, db_connection, db_cur):
    setup_data(db_connection, db_cur)
    request = {
        "requests": [
            {"collection": "a", "ids": [1], "mapped_fields": ["field_1"]},
            {
                "collection": "b",
                "ids": [1, 2],
                "mapped_fields": ["field_4", "field_5"],
            },
        ],
        "mapped_fields": ["common_field"],
    }
    response = json_client.post(Route.GET_MANY.URL, request)
    assert_success_response(response)
    assert response.json == {
        "a/1": {"field_1": "data", "common_field": 1},
        "b/1": {"field_4": "data", "field_5": 42, "common_field": 2},
        "b/2": {"field_4": "data", "field_5": 42, "common_field": 3},
    }


def test_partial_mapped_fields(json_client, db_connection, db_cur):
    setup_data(db_connection, db_cur)
    request = {
        "requests": [
            {"collection": "a", "ids": [1], "mapped_fields": ["field_1"]},
            {"collection": "b", "ids": [1]},
        ],
    }
    response = json_client.post(Route.GET_MANY.URL, request)
    assert_success_response(response)
    assert response.json == {
        "a/1": {"field_1": "data"},
        "b/1": data["b/1"],
    }


def test_same_collection(json_client, db_connection, db_cur):
    setup_data(db_connection, db_cur)
    request = {
        "requests": [
            {"collection": "b", "ids": [1], "mapped_fields": ["field_4"]},
            {"collection": "b", "ids": [2], "mapped_fields": ["field_5"]},
        ],
    }
    response = json_client.post(Route.GET_MANY.URL, request)
    assert_success_response(response)
    assert response.json == {
        "b/1": {"field_4": "data"},
        "b/2": {"field_5": 42},
    }


def test_fqfields(json_client, db_connection, db_cur):
    setup_data(db_connection, db_cur)
    request = {
        "requests": ["b/1/field_4", "b/2/field_5"],
    }
    response = json_client.post(Route.GET_MANY.URL, request)
    assert_success_response(response)
    assert response.json == {
        "b/1": {"field_4": "data"},
        "b/2": {"field_5": 42},
    }


def setup_events_data(connection, cursor):
    cursor.execute(
        "insert into positions (user_id) values (0), (0), (0), (0), (0), (0)"
    )
    for fqid, model in data.items():
        cursor.execute(
            "insert into events (position, fqid, type, data) values (1, %s, %s, %s)",
            [fqid, EVENT_TYPES.CREATE, json.dumps(model)],
        )
        cursor.execute(
            "insert into events (position, fqid, type, data) values (2, %s, %s, %s)",
            [fqid, EVENT_TYPES.UPDATE, json.dumps({"common_field": 0})],
        )
    connection.commit()


def test_position(json_client, db_connection, db_cur):
    setup_events_data(db_connection, db_cur)
    request = {
        "requests": default_request_parts,
        "position": 1,
    }
    response = json_client.post(Route.GET_MANY.URL, request)
    assert_success_response(response)
    assert response.json == {
        "a/1": {
            "field_1": "data",
            "field_2": 42,
            "field_3": [1, 2, 3],
            "common_field": 1,
            "meta_position": 1,
        },
        "b/1": {
            "field_4": "data",
            "field_5": 42,
            "field_6": [1, 2, 3],
            "common_field": 2,
            "meta_position": 1,
        },
        "b/2": {
            "field_4": "data",
            "field_5": 42,
            "field_6": [1, 2, 3],
            "common_field": 3,
            "meta_position": 1,
        },
    }


def test_position_deleted(json_client, db_connection, db_cur):
    setup_events_data(db_connection, db_cur)
    db_cur.execute(
        "insert into events (position, fqid, type) values (3, %s, %s)",
        ["b/1", EVENT_TYPES.DELETE],
    )
    db_cur.execute(
        "insert into events (position, fqid, type) values (4, %s, %s)",
        ["b/1", EVENT_TYPES.RESTORE],
    )
    db_connection.commit()
    request = {
        "requests": default_request_parts,
        "position": 3,
    }
    response = json_client.post(Route.GET_MANY.URL, request)
    assert response.json == {
        "a/1": {
            "field_1": "data",
            "field_2": 42,
            "field_3": [1, 2, 3],
            "common_field": 0,
            "meta_position": 2,
        },
        "b/2": {
            "field_4": "data",
            "field_5": 42,
            "field_6": [1, 2, 3],
            "common_field": 0,
            "meta_position": 2,
        },
    }


def test_position_not_deleted(json_client, db_connection, db_cur):
    setup_events_data(db_connection, db_cur)
    db_cur.execute(
        "insert into events (position, fqid, type) values (3, %s, %s)",
        ["b/1", EVENT_TYPES.DELETE],
    )
    db_connection.commit()
    request = {
        "requests": default_request_parts,
        "position": 3,
        "get_deleted_models": DeletedModelsBehaviour.ONLY_DELETED,
    }
    response = json_client.post(Route.GET_MANY.URL, request)
    assert response.json == {
        "b/1": {
            "field_4": "data",
            "field_5": 42,
            "field_6": [1, 2, 3],
            "common_field": 0,
            "meta_position": 2,
        },
    }


def test_position_mapped_fields(json_client, db_connection, db_cur):
    setup_events_data(db_connection, db_cur)
    request = {
        "requests": [
            {"collection": "a", "ids": [1], "mapped_fields": ["field_1"]},
            {
                "collection": "b",
                "ids": [1, 2],
                "mapped_fields": ["field_4", "field_5"],
            },
        ],
        "position": 1,
        "mapped_fields": ["common_field"],
    }
    response = json_client.post(Route.GET_MANY.URL, request)
    assert_success_response(response)
    assert response.json == {
        "a/1": {"field_1": "data", "common_field": 1},
        "b/1": {"field_4": "data", "field_5": 42, "common_field": 2},
        "b/2": {"field_4": "data", "field_5": 42, "common_field": 3},
    }


def test_negative_id(json_client):
    request = {
        "requests": [{"collection": "a", "ids": [-1]}],
    }
    response = json_client.post(Route.GET_MANY.URL, request)
    assert_error_response(response, ERROR_CODES.INVALID_FORMAT)


def test_invalid_collection(json_client):
    request = {
        "requests": [{"collection": "not valid", "ids": [1]}],
    }
    response = json_client.post(Route.GET_MANY.URL, request)
    assert_error_response(response, ERROR_CODES.INVALID_FORMAT)
