import json
import copy

from shared.core import DeletedModelsBehaviour
from shared.postgresql_backend import EVENT_TYPES
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
    assert response.json == data


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
    assert response.json == data


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
    assert response.json == {}


def test_no_deleted(json_client, db_connection, db_cur):
    setup_data(db_connection, db_cur, True)
    response = json_client.post(GET_MANY_URL, default_request)
    assert_success_response(response)
    assert response.json == {}


def test_deleted(json_client, db_connection, db_cur):
    setup_data(db_connection, db_cur, True)
    request = {
        "requests": default_request_parts,
        "get_deleted_models": DeletedModelsBehaviour.ONLY_DELETED,
    }
    response = json_client.post(GET_MANY_URL, request)
    assert_success_response(response)
    assert response.json == data


def test_deleted_not_deleted(json_client, db_connection, db_cur):
    setup_data(db_connection, db_cur)
    request = {
        "requests": default_request_parts,
        "get_deleted_models": DeletedModelsBehaviour.ONLY_DELETED,
    }
    response = json_client.post(GET_MANY_URL, request)
    assert_success_response(response)
    assert response.json == {}


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
    assert response.json == {
        "c1/1": {"field_1": "data", "meta_position": 1},
        "c2/1": {"field_4": "data", "field_5": 42, "meta_position": 2},
        "c2/2": {"field_4": "data", "field_5": 42, "meta_position": 3},
    }


def setup_events_data(connection, cursor):
    cursor.execute("insert into positions (user_id) values (0), (0), (0), (0), (0), (0)")
    for fqid, model in data.items():
        cursor.execute("insert into events (position, fqid, type, data) values (1, %s, %s, %s)", [fqid, EVENT_TYPES.CREATE, json.dumps(model)])
        cursor.execute("insert into events (position, fqid, type, data) values (2, %s, %s, %s)", [fqid, EVENT_TYPES.UPDATE, json.dumps({"meta_position": 0})])
    connection.commit()


def test_position(json_client, db_connection, db_cur):
    setup_events_data(db_connection, db_cur)
    request = {
        "requests": default_request_parts,
        "position": 1,
    }
    response = json_client.post(GET_MANY_URL, request)
    assert_success_response(response)
    assert response.json == data


def test_position_deleted(json_client, db_connection, db_cur):
    setup_events_data(db_connection, db_cur)
    db_cur.execute("insert into events (position, fqid, type) values (3, %s, %s)", ["c2/1", EVENT_TYPES.DELETE])
    db_connection.commit()
    request = {
        "requests": default_request_parts,
        "position": 3,
    }
    response = json_client.post(GET_MANY_URL, request)
    assert response.json == {
        "c1/1": {
            "field_1": "data",
            "field_2": 42,
            "field_3": [1, 2, 3],
            "meta_position": 0,
        },
        "c2/2": {
            "field_4": "data",
            "field_5": 42,
            "field_6": [1, 2, 3],
            "meta_position": 0,
        },
    }


def test_position_not_deleted(json_client, db_connection, db_cur):
    setup_events_data(db_connection, db_cur)
    db_cur.execute("insert into events (position, fqid, type) values (3, %s, %s)", ["c2/1", EVENT_TYPES.DELETE])
    db_connection.commit()
    request = {
        "requests": default_request_parts,
        "position": 3,
        "get_deleted_models": DeletedModelsBehaviour.ONLY_DELETED,
    }
    response = json_client.post(GET_MANY_URL, request)
    assert response.json == {
        "c2/1": {
            "field_4": "data",
            "field_5": 42,
            "field_6": [1, 2, 3],
            "meta_position": 0,
        },
    }


def test_position_mapped_fields(json_client, db_connection, db_cur):
    setup_events_data(db_connection, db_cur)
    request = {
        "requests": default_request_parts,
        "position": 1,
        "mapped_fields": ["meta_position"],
    }
    response = json_client.post(GET_MANY_URL, request)
    assert_success_response(response)
    assert response.json == {
        "c1/1": {"meta_position": 1},
        "c2/1": {"meta_position": 2},
        "c2/2": {"meta_position": 3},
    }
