import json

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


def setup_data(connection, cursor):
    for fqid, model in data.items():
        cursor.execute("insert into models values (%s, %s)", [fqid, json.dumps(model)])
        cursor.execute("insert into models_lookup values (%s, FALSE)", [fqid])
    connection.commit()


def test_simple(json_client, db_connection, db_cur):
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
