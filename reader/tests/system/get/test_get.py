import json

from reader.flask_frontend.routes import Route
from shared.flask_frontend.errors import ERROR_CODES
from shared.postgresql_backend import EVENT_TYPES
from shared.tests.util import assert_error_response, assert_success_response
from shared.util import DeletedModelsBehaviour


FQID = "collection/1"
data = {
    "fqid": FQID,
    "field_1": "data",
    "field_2": 42,
    "field_3": [1, 2, 3],
    "meta_position": 1,
}
data_json = json.dumps(data)


def setup_data(connection, cursor, deleted=False):
    cursor.execute("insert into models values ('collection/1', %s)", [data_json])
    cursor.execute("insert into models_lookup values ('collection/1', %s)", [deleted])
    connection.commit()


def test_simple(json_client, db_connection, db_cur):
    setup_data(db_connection, db_cur)
    response = json_client.post(Route.GET.URL, {"fqid": FQID})
    assert_success_response(response)
    assert response.json == data


def test_no_model(json_client, db_connection, db_cur):
    response = json_client.post(Route.GET.URL, {"fqid": FQID})
    assert_error_response(response, ERROR_CODES.MODEL_DOES_NOT_EXIST)


def test_get_no_deleted_success(json_client, db_connection, db_cur):
    setup_data(db_connection, db_cur)
    response = json_client.post(
        Route.GET.URL,
        {"fqid": FQID, "get_deleted_models": DeletedModelsBehaviour.NO_DELETED},
    )
    assert_success_response(response)
    assert response.json == data


def test_get_no_deleted_fail(json_client, db_connection, db_cur):
    setup_data(db_connection, db_cur, True)
    response = json_client.post(
        Route.GET.URL,
        {"fqid": FQID, "get_deleted_models": DeletedModelsBehaviour.NO_DELETED},
    )
    assert_error_response(response, ERROR_CODES.MODEL_DOES_NOT_EXIST)


def test_get_only_deleted_success(json_client, db_connection, db_cur):
    setup_data(db_connection, db_cur, True)
    response = json_client.post(
        Route.GET.URL,
        {"fqid": FQID, "get_deleted_models": DeletedModelsBehaviour.ONLY_DELETED},
    )
    assert_success_response(response)
    assert response.json == data


def test_get_only_deleted_fail(json_client, db_connection, db_cur):
    setup_data(db_connection, db_cur)
    response = json_client.post(
        Route.GET.URL,
        {"fqid": FQID, "get_deleted_models": DeletedModelsBehaviour.ONLY_DELETED},
    )
    assert_error_response(response, ERROR_CODES.MODEL_NOT_DELETED)


def test_get_all_models_not_deleted(json_client, db_connection, db_cur):
    setup_data(db_connection, db_cur)
    response = json_client.post(
        Route.GET.URL,
        {"fqid": FQID, "get_deleted_models": DeletedModelsBehaviour.ALL_MODELS},
    )
    assert_success_response(response)
    assert response.json == data


def test_get_all_models_deleted(json_client, db_connection, db_cur):
    setup_data(db_connection, db_cur, True)
    response = json_client.post(
        Route.GET.URL,
        {"fqid": FQID, "get_deleted_models": DeletedModelsBehaviour.ALL_MODELS},
    )
    assert_success_response(response)
    assert response.json == data


def test_get_all_models_no_model(json_client, db_connection, db_cur):
    response = json_client.post(
        Route.GET.URL,
        {"fqid": FQID, "get_deleted_models": DeletedModelsBehaviour.ALL_MODELS},
    )
    assert_error_response(response, ERROR_CODES.MODEL_DOES_NOT_EXIST)


def test_mapped_fields(json_client, db_connection, db_cur):
    setup_data(db_connection, db_cur)
    response = json_client.post(
        Route.GET.URL, {"fqid": FQID, "mapped_fields": ["fqid", "field_3"]}
    )
    assert_success_response(response)
    assert response.json == {
        "fqid": FQID,
        "field_3": [1, 2, 3],
    }


def setup_events_data(connection, cursor):
    cursor.execute("insert into positions (user_id) values (0), (0), (0), (0), (0)")
    cursor.execute(
        "insert into events (position, fqid, type, data) values (1, %s, %s, %s)",
        [FQID, EVENT_TYPES.CREATE, data_json],
    )
    cursor.execute(
        "insert into events (position, fqid, type, data) values (2, %s, %s, %s)",
        [FQID, EVENT_TYPES.UPDATE, json.dumps({"field_1": "other"})],
    )
    connection.commit()


def test_position(json_client, db_connection, db_cur):
    setup_events_data(db_connection, db_cur)
    response = json_client.post(Route.GET.URL, {"fqid": FQID, "position": 1})
    assert_success_response(response)
    assert response.json == data


def test_position_deleted(json_client, db_connection, db_cur):
    setup_events_data(db_connection, db_cur)
    db_cur.execute(
        "insert into events (position, fqid, type) values (3, %s, %s)",
        [FQID, EVENT_TYPES.DELETE],
    )
    db_connection.commit()
    response = json_client.post(Route.GET.URL, {"fqid": FQID, "position": 3})
    assert_error_response(response, ERROR_CODES.MODEL_DOES_NOT_EXIST)


def test_position_not_deleted(json_client, db_connection, db_cur):
    setup_events_data(db_connection, db_cur)
    response = json_client.post(
        Route.GET.URL,
        {
            "fqid": FQID,
            "position": 1,
            "get_deleted_models": DeletedModelsBehaviour.ONLY_DELETED,
        },
    )
    assert_error_response(response, ERROR_CODES.MODEL_NOT_DELETED)


def test_position_mapped_fields(json_client, db_connection, db_cur):
    setup_events_data(db_connection, db_cur)
    response = json_client.post(
        Route.GET.URL, {"fqid": FQID, "position": 1, "mapped_fields": ["field_1"]}
    )
    assert_success_response(response)
    assert response.json == {"field_1": "data"}


def test_invalid_fqid(json_client):
    response = json_client.post(Route.GET.URL, {"fqid": "not valid"})
    assert_error_response(response, ERROR_CODES.INVALID_FORMAT)


def test_invalid_mapped_fields(json_client):
    response = json_client.post(
        Route.GET.URL, {"fqid": FQID, "mapped_fields": ["not valid"]}
    )
    assert_error_response(response, ERROR_CODES.INVALID_FORMAT)


def test_invalid_position(json_client):
    response = json_client.post(Route.GET.URL, {"fqid": FQID, "position": 0})
    assert_error_response(response, ERROR_CODES.INVALID_FORMAT)
