import json

from reader.flask_frontend.routes import Route
from shared.tests.util import assert_success_response


data = {
    "c1/1": {"field_1": "data", "field_2": 42, "field_3": True, "meta_position": 1},
    "c1/2": {"field_1": "test", "field_2": 21, "field_3": False, "meta_position": 2},
}
other_models = {
    "c2/1": {"field_4": "data", "field_5": 42, "field_6": True, "meta_position": 3}
}


def setup_data(connection, cursor, deleted=False):
    for fqid, model in list(data.items()) + list(other_models.items()):
        cursor.execute("insert into models values (%s, %s)", [fqid, json.dumps(model)])
        cursor.execute("insert into models_lookup values (%s, %s)", [fqid, deleted])
    connection.commit()


def test_eq(json_client, db_connection, db_cur):
    setup_data(db_connection, db_cur)
    response = json_client.post(
        Route.FILTER.URL,
        {
            "collection": "c1",
            "filter": {"field": "field_1", "operator": "=", "value": "data"},
        },
    )
    assert_success_response(response)
    assert response.json == [data["c1/1"]]


def test_gt(json_client, db_connection, db_cur):
    setup_data(db_connection, db_cur)
    response = json_client.post(
        Route.FILTER.URL,
        {
            "collection": "c1",
            "filter": {"field": "field_2", "operator": ">", "value": 21},
        },
    )
    assert_success_response(response)
    assert response.json == [data["c1/1"]]


def test_geq(json_client, db_connection, db_cur):
    setup_data(db_connection, db_cur)
    response = json_client.post(
        Route.FILTER.URL,
        {
            "collection": "c1",
            "filter": {"field": "field_2", "operator": ">=", "value": 21},
        },
    )
    assert_success_response(response)
    assert response.json == list(data.values())


def test_neq(json_client, db_connection, db_cur):
    setup_data(db_connection, db_cur)
    response = json_client.post(
        Route.FILTER.URL,
        {
            "collection": "c1",
            "filter": {"field": "field_2", "operator": "!=", "value": 21},
        },
    )
    assert_success_response(response)
    assert response.json == [data["c1/1"]]


def test_lt(json_client, db_connection, db_cur):
    setup_data(db_connection, db_cur)
    response = json_client.post(
        Route.FILTER.URL,
        {
            "collection": "c1",
            "filter": {"field": "field_2", "operator": "<", "value": 42},
        },
    )
    assert_success_response(response)
    assert response.json == [data["c1/2"]]


def test_leq(json_client, db_connection, db_cur):
    setup_data(db_connection, db_cur)
    response = json_client.post(
        Route.FILTER.URL,
        {
            "collection": "c1",
            "filter": {"field": "field_2", "operator": "<=", "value": 42},
        },
    )
    assert_success_response(response)
    assert response.json == list(data.values())


def test_and(json_client, db_connection, db_cur):
    setup_data(db_connection, db_cur)
    response = json_client.post(
        Route.FILTER.URL,
        {
            "collection": "c1",
            "filter": {
                "and_filter": [
                    {"field": "field_1", "operator": "=", "value": "data"},
                    {"field": "field_2", "operator": "=", "value": 42},
                ]
            },
        },
    )
    assert_success_response(response)
    assert response.json == [data["c1/1"]]


def test_or(json_client, db_connection, db_cur):
    setup_data(db_connection, db_cur)
    response = json_client.post(
        Route.FILTER.URL,
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


def test_complex(json_client, db_connection, db_cur):
    setup_data(db_connection, db_cur)
    # (field_1 == 'data' and field_2 > 21) or (field_3 == False and not field_2 < 21)
    response = json_client.post(
        Route.FILTER.URL,
        {
            "collection": "c1",
            "filter": {
                "or_filter": [
                    {
                        "and_filter": [
                            {"field": "field_1", "operator": "=", "value": "data"},
                            {"field": "field_2", "operator": ">", "value": 21},
                        ]
                    },
                    {
                        "and_filter": [
                            {"field": "field_3", "operator": "=", "value": False},
                            {
                                "not_filter": {
                                    "field": "field_2",
                                    "operator": "<",
                                    "value": 21,
                                }
                            },
                        ]
                    },
                ],
            },
        },
    )
    assert_success_response(response)
    assert response.json == list(data.values())


def test_invalid_field(json_client, db_connection, db_cur):
    setup_data(db_connection, db_cur)
    response = json_client.post(
        Route.FILTER.URL,
        {
            "collection": "c1",
            "filter": {"field": "invalid", "operator": "=", "value": "data"},
        },
    )
    assert_success_response(response)
    assert response.json == []


def test_mapped_fields(json_client, db_connection, db_cur):
    setup_data(db_connection, db_cur)
    response = json_client.post(
        Route.FILTER.URL,
        {
            "collection": "c1",
            "filter": {"field": "field_1", "operator": "=", "value": "data"},
            "mapped_fields": ["field_3", "meta_position"],
        },
    )
    assert_success_response(response)
    assert response.json == [{"field_3": True, "meta_position": 1}]