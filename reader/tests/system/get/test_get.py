import copy
import json

from shared.core import DeletedModelsBehaviour
from shared.flask_frontend.errors import ERROR_CODES
from shared.tests.util import assert_error_response, assert_success_response
from tests.system.util import GET_URL


FQID = "collection/1"
data = {
    "fqid": FQID,
    "field_1": "data",
    "field_2": 42,
    "field_3": [1, 2, 3],
}
data_json = json.dumps(data)


def setup_data(connection, cursor, deleted=False):
    cursor.execute("insert into models values ('collection/1', %s)", [data_json])
    cursor.execute("insert into models_lookup values ('collection/1', %s)", [deleted])
    connection.commit()


def test_simple(json_client, db_connection, db_cur):
    setup_data(db_connection, db_cur)
    response = json_client.post(GET_URL, {"fqid": FQID})
    assert_success_response(response)
    assert response.json == data


def test_no_model(json_client, db_connection, db_cur):
    response = json_client.post(GET_URL, {"fqid": FQID})
    assert_error_response(response, ERROR_CODES.MODEL_DOES_NOT_EXIST)


def test_get_no_deleted_success(json_client, db_connection, db_cur):
    setup_data(db_connection, db_cur)
    response = json_client.post(
        GET_URL, {"fqid": FQID, "get_deleted_models": DeletedModelsBehaviour.NO_DELETED}
    )
    assert_success_response(response)
    assert response.json == data


def test_get_no_deleted_fail(json_client, db_connection, db_cur):
    setup_data(db_connection, db_cur, True)
    response = json_client.post(
        GET_URL, {"fqid": FQID, "get_deleted_models": DeletedModelsBehaviour.NO_DELETED}
    )
    assert_error_response(response, ERROR_CODES.MODEL_DOES_NOT_EXIST)


def test_get_only_deleted_success(json_client, db_connection, db_cur):
    setup_data(db_connection, db_cur, True)
    response = json_client.post(
        GET_URL,
        {"fqid": FQID, "get_deleted_models": DeletedModelsBehaviour.ONLY_DELETED},
    )
    assert_success_response(response)
    assert response.json == data


def test_get_only_deleted_fail(json_client, db_connection, db_cur):
    setup_data(db_connection, db_cur, True)
    response = json_client.post(
        GET_URL,
        {"fqid": FQID, "get_deleted_models": DeletedModelsBehaviour.ONLY_DELETED},
    )
    assert_success_response(response)
    assert response.json == data


def test_get_all_models_not_deleted(json_client, db_connection, db_cur):
    setup_data(db_connection, db_cur)
    response = json_client.post(
        GET_URL, {"fqid": FQID, "get_deleted_models": DeletedModelsBehaviour.ALL_MODELS}
    )
    assert_success_response(response)
    assert response.json == data


def test_get_all_models_deleted(json_client, db_connection, db_cur):
    setup_data(db_connection, db_cur, True)
    response = json_client.post(
        GET_URL, {"fqid": FQID, "get_deleted_models": DeletedModelsBehaviour.ALL_MODELS}
    )
    assert_success_response(response)
    assert response.json == data


def test_get_all_models_no_model(json_client, db_connection, db_cur):
    response = json_client.post(
        GET_URL, {"fqid": FQID, "get_deleted_models": DeletedModelsBehaviour.ALL_MODELS}
    )
    assert_error_response(response, ERROR_CODES.MODEL_DOES_NOT_EXIST)


def test_mapped_fields(json_client, db_connection, db_cur):
    setup_data(db_connection, db_cur)
    response = json_client.post(
        GET_URL, {"fqid": FQID, "mapped_fields": ["fqid", "field_3"]}
    )
    assert_success_response(response)
    mapped_data = copy.deepcopy(data)
    del mapped_data["field_1"]
    del mapped_data["field_2"]
    assert response.json == mapped_data
