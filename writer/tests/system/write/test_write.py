import copy

import pytest

from shared.flask_frontend import ERROR_CODES
from shared.tests.util import assert_error_response
from tests.system.util import (
    WRITE_URL,
    assert_model,
    assert_modified_fields,
    assert_no_db_entry,
    assert_no_model,
    assert_no_modified_fields,
)


@pytest.fixture()
def data():
    yield copy.deepcopy(
        {
            "user_id": 1,
            "information": {},
            "locked_fields": {},
            "events": [{"type": "create", "fqid": "a/1", "fields": {"f": 1}}],
        }
    )


def create_model(json_client, data, redis_connection, reset_redis_data):
    response = json_client.post(WRITE_URL, data)
    assert response.status_code == 200
    assert_model("a/1", {"f": 1}, 1)
    assert_modified_fields(redis_connection, {"a/1": ["f"]})
    reset_redis_data()


def test_create_simple(json_client, data, redis_connection, reset_redis_data):
    create_model(json_client, data, redis_connection, reset_redis_data)


def test_create_empty_field(json_client, data, redis_connection):
    data["events"][0]["fields"]["empty"] = None
    response = json_client.post(WRITE_URL, data)
    assert response.status_code == 200
    assert_model("a/1", {"f": 1}, 1)
    assert_modified_fields(redis_connection, {"a/1": ["f"]})


def test_create_twice(json_client, data, db_cur, redis_connection):
    data["events"].append(data["events"][0])
    response = json_client.post(WRITE_URL, data)
    assert_error_response(response, ERROR_CODES.MODEL_EXISTS)
    assert_no_db_entry(db_cur)
    assert_no_modified_fields(redis_connection)


def test_create_update(json_client, data, redis_connection):
    field_data = [True, None, {"test": "value"}]
    data["events"].append(
        {
            "type": "update",
            "fqid": "a/1",
            "fields": {"f": None, "another_field": field_data},
        }
    )
    response = json_client.post(WRITE_URL, data)
    assert response.status_code == 200
    assert_model("a/1", {"another_field": field_data}, 1)
    assert_modified_fields(redis_connection, {"a/1": ["f", "another_field"]})


def test_single_update(json_client, data, redis_connection, reset_redis_data):
    create_model(json_client, data, redis_connection, reset_redis_data)

    field_data = [True, None, {"test": "value"}]
    data["events"][0] = {
        "type": "update",
        "fqid": "a/1",
        "fields": {"f": None, "another_field": field_data},
    }
    response = json_client.post(WRITE_URL, data)
    assert response.status_code == 200
    assert_model("a/1", {"another_field": field_data}, 2)
    assert_modified_fields(
        redis_connection, {"a/1": ["f", "another_field"]}, meta_deleted=False
    )


def test_update_non_existing_1(json_client, data, db_cur, redis_connection):
    data["events"][0] = {"type": "update", "fqid": "a/1", "fields": {"f": "value"}}
    response = json_client.post(WRITE_URL, data)
    assert_error_response(response, ERROR_CODES.MODEL_DOES_NOT_EXIST)
    assert_no_db_entry(db_cur)
    assert_no_modified_fields(redis_connection)


def test_update_non_existing_2(json_client, data, db_cur, redis_connection):
    data["events"][0] = {"type": "update", "fqid": "a/1", "fields": {"f": None}}
    response = json_client.post(WRITE_URL, data)
    assert_error_response(response, ERROR_CODES.MODEL_DOES_NOT_EXIST)
    assert_no_db_entry(db_cur)
    assert_no_modified_fields(redis_connection)


def test_create_delete(json_client, data, redis_connection, reset_redis_data):
    data["events"].append({"type": "delete", "fqid": "a/1"})
    response = json_client.post(WRITE_URL, data)
    assert response.status_code == 200
    assert_no_model("a/1")
    assert_modified_fields(redis_connection, {"a/1": ["f"]})


def test_single_delete(json_client, data, redis_connection, reset_redis_data):
    create_model(json_client, data, redis_connection, reset_redis_data)

    data["events"][0] = {"type": "delete", "fqid": "a/1"}
    response = json_client.post(WRITE_URL, data)
    assert response.status_code == 200
    assert_no_model("a/1")
    assert_modified_fields(redis_connection, {"a/1": ["f"]})


def test_delete_model_does_not_exist(
    json_client, data, redis_connection, reset_redis_data
):
    data["events"][0] = {"type": "delete", "fqid": "a/1"}
    response = json_client.post(WRITE_URL, data)
    assert_error_response(response, ERROR_CODES.MODEL_DOES_NOT_EXIST)
    assert_no_model("a/1")
    assert_no_modified_fields(redis_connection)


def test_create_delete_restore(json_client, data, redis_connection):
    data["events"].append({"type": "delete", "fqid": "a/1"})
    data["events"].append({"type": "restore", "fqid": "a/1"})
    response = json_client.post(WRITE_URL, data)
    assert response.status_code == 200
    assert_model("a/1", {"f": 1}, 1)
    assert_modified_fields(redis_connection, {"a/1": ["f"]})


def test_single_restore(json_client, data, redis_connection, reset_redis_data):
    data["events"].append({"type": "delete", "fqid": "a/1"})
    response = json_client.post(WRITE_URL, data)
    assert response.status_code == 200
    assert_no_model("a/1")
    assert_modified_fields(redis_connection, {"a/1": ["f"]})
    reset_redis_data()

    data["events"] = [{"type": "restore", "fqid": "a/1"}]
    response = json_client.post(WRITE_URL, data)
    assert response.status_code == 200
    assert_model("a/1", {"f": 1}, 2)
    assert_modified_fields(redis_connection, {"a/1": ["f"]})


def test_restore_without_delete(json_client, data, redis_connection, reset_redis_data):
    response = json_client.post(WRITE_URL, data)
    assert response.status_code == 200
    assert_model("a/1", {"f": 1}, 1)
    assert_modified_fields(redis_connection, {"a/1": ["f"]})
    reset_redis_data()

    data["events"] = [{"type": "restore", "fqid": "a/1"}]
    response = json_client.post(WRITE_URL, data)
    assert_error_response(response, ERROR_CODES.MODEL_NOT_DELETED)
    assert_model("a/1", {"f": 1}, 1)
    assert_no_modified_fields(redis_connection)


def test_create_delete_restore_different_positions(
    json_client, data, redis_connection, reset_redis_data
):
    create_model(json_client, data, redis_connection, reset_redis_data)

    data["events"][0] = {"type": "delete", "fqid": "a/1"}
    response = json_client.post(WRITE_URL, data)
    assert response.status_code == 200
    assert_no_model("a/1")
    assert_modified_fields(redis_connection, {"a/1": ["f"]})
    reset_redis_data()

    data["events"][0] = {"type": "restore", "fqid": "a/1"}

    response = json_client.post(WRITE_URL, data)
    assert response.status_code == 200
    assert_model("a/1", {"f": 1}, 3)
    assert_modified_fields(redis_connection, {"a/1": ["f"]})


def test_delete_restore_delete_restore(
    json_client, data, redis_connection, reset_redis_data
):
    create_model(json_client, data, redis_connection, reset_redis_data)

    data["events"][0] = {"type": "delete", "fqid": "a/1"}
    data["events"].append({"type": "restore", "fqid": "a/1"})
    data["events"].append({"type": "delete", "fqid": "a/1"})
    data["events"].append({"type": "restore", "fqid": "a/1"})
    response = json_client.post(WRITE_URL, data)
    assert response.status_code == 200
    assert_model("a/1", {"f": 1}, 2)
    assert_modified_fields(redis_connection, {"a/1": ["f"]})


def test_update_delete_restore_update(
    json_client, data, redis_connection, reset_redis_data
):
    create_model(json_client, data, redis_connection, reset_redis_data)

    data["events"][0] = {
        "type": "update",
        "fqid": "a/1",
        "fields": {"another": "value", "f": None},
    }
    data["events"].append({"type": "delete", "fqid": "a/1"})
    data["events"].append({"type": "restore", "fqid": "a/1"})
    data["events"].append(
        {"type": "update", "fqid": "a/1", "fields": {"third_field": ["my", "list"]}}
    )
    response = json_client.post(WRITE_URL, data)
    assert response.status_code == 200
    assert_model("a/1", {"another": "value", "third_field": ["my", "list"]}, 2)
    assert_modified_fields(redis_connection, {"a/1": ["f", "another", "third_field"]})
