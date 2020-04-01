import json

from shared.tests.util import assert_success_response
from tests.system.util import FILTER_URL


data = {
    "c1/1": {
        "field_1": "data",
        "field_2": 42,
        "field_3": [1, 2, 3],
        "meta_position": 1,
    },
    "c1/2": {
        "field_1": "test",
        "field_2": 42,
        "field_3": [1, 2, 3],
        "meta_position": 2,
    },
}
other_models = {
    "c2/1": {
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


def test_simple(json_client, db_connection, db_cur):
    setup_data(db_connection, db_cur)
    response = json_client.post(
        FILTER_URL,
        {
            "collection": "c1",
            "filter": {"field": "field_1", "operator": "=", "value": "data"},
        },
    )
    assert_success_response(response)
    assert response.json == [data["c1/1"]]


def test_and(json_client, db_connection, db_cur):
    setup_data(db_connection, db_cur)
    response = json_client.post(
        FILTER_URL,
        {
            "collection": "c1",
            "filter": {
                "and_filter": [
                    {"field": "field_1", "operator": "=", "value": "data"},
                    {"field": "field_2", "operator": "=", "value": "42"},
                ]
            },
        },
    )
    assert_success_response(response)
    assert response.json == [data["c1/1"]]


def test_or(json_client, db_connection, db_cur):
    setup_data(db_connection, db_cur)
    response = json_client.post(
        FILTER_URL,
        {
            "collection": "c1",
            "filter": {
                "or_filter": [
                    {"field": "field_1", "operator": "=", "value": "data"},
                    {"field": "field_1", "operator": "=", "value": "test"},
                ]
            },
        },
    )
    assert_success_response(response)
    assert response.json == list(data.values())
