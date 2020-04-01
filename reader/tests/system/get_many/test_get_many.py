import json

from shared.core import DeletedModelsBehaviour
from shared.tests.util import assert_success_response
from tests.system.util import GET_MANY_URL


data = {
    "c1/1": {
        "field_1": "data",
        "field_2": 42,
        "field_3": [1, 2, 3],
        "meta_position": 1,
    },
    "c2/1": {
        "field_4": "data",
        "field_5": 42,
        "field_6": [1, 2, 3],
        "meta_position": 2,
    },
    "c2/2": {
        "field_4": "data",
        "field_5": 42,
        "field_6": [1, 2, 3],
        "meta_position": 3,
    },
}
default_request_parts = [
    {"collection": "c1", "ids": [1]},
    {"collection": "c2", "ids": [1, 2]},
]
default_request = {"requests": default_request_parts}


def setup_data(connection, cursor, deleted=False):
    for fqid, model in data.items():
        cursor.execute("insert into models values (%s, %s)", [fqid, json.dumps(model)])
        cursor.execute("insert into models_lookup values (%s, %s)", [fqid, deleted])
    connection.commit()


def test_simple(json_client, db_connection, db_cur):
    setup_data(db_connection, db_cur)
    response = json_client.post(GET_MANY_URL, default_request)
    assert_success_response(response)
    assert response.json == list(data.values())


def test_invalid_fqids(json_client, db_connection, db_cur):
    setup_data(db_connection, db_cur)
    request = {
        "requests": [
            {"collection": "c1", "ids": [1]},
            {"collection": "c2", "ids": [1, 2, 3]},
            {"collection": "c3", "ids": [1]},
        ],
    }
    response = json_client.post(GET_MANY_URL, request)
    assert_success_response(response)
    assert response.json == list(data.values())


def test_only_invalid_fqids(json_client, db_connection, db_cur):
    setup_data(db_connection, db_cur)
    request = {
        "requests": [
            {"collection": "c2", "ids": [3]},
            {"collection": "c3", "ids": [1]},
        ],
    }
    response = json_client.post(GET_MANY_URL, request)
    assert_success_response(response)
    assert response.json == []


def test_no_deleted(json_client, db_connection, db_cur):
    setup_data(db_connection, db_cur, True)
    response = json_client.post(GET_MANY_URL, default_request)
    assert_success_response(response)
    assert response.json == []


def test_deleted(json_client, db_connection, db_cur):
    setup_data(db_connection, db_cur, True)
    request = {
        "requests": default_request_parts,
        "get_deleted_models": DeletedModelsBehaviour.ONLY_DELETED,
    }
    response = json_client.post(GET_MANY_URL, request)
    assert_success_response(response)
    assert response.json == list(data.values())


def test_deleted_not_deleted(json_client, db_connection, db_cur):
    setup_data(db_connection, db_cur)
    request = {
        "requests": default_request_parts,
        "get_deleted_models": DeletedModelsBehaviour.ONLY_DELETED,
    }
    response = json_client.post(GET_MANY_URL, request)
    assert_success_response(response)
    assert response.json == []


def test_mapped_fields(json_client, db_connection, db_cur):
    setup_data(db_connection, db_cur)
    request = {
        "requests": [
            {"collection": "c1", "ids": [1], "mapped_fields": ["field_1"]},
            {
                "collection": "c2",
                "ids": [1, 2],
                "mapped_fields": ["field_4", "field_5"],
            },
        ],
        "mapped_fields": ["meta_position"],
    }
    response = json_client.post(GET_MANY_URL, request)
    assert_success_response(response)
    assert response.json == [
        {"field_1": "data", "meta_position": 1},
        {"field_4": "data", "field_5": 42, "meta_position": 2},
        {"field_4": "data", "field_5": 42, "meta_position": 3},
    ]
