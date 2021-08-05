import copy

import pytest

from datastore.shared.flask_frontend import ERROR_CODES
from datastore.writer.flask_frontend.routes import WRITE_URL
from tests.util import assert_error_response, assert_response_code
from tests.writer.system.util import (
    assert_model,
    assert_modified_fields,
    assert_no_model,
    assert_no_modified_fields,
)

from .test_write import create_model


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


def test_restore_x(json_client, data, redis_connection, reset_redis_data):
    data["events"].append({"type": "delete", "fqid": "a/1"})
    response = json_client.post(WRITE_URL, data)
    assert_response_code(response, 201)
    assert_no_model("a/1")
    assert_modified_fields(redis_connection, {"a/1": ["f"]})
    reset_redis_data()

    data["events"] = [{"type": "restore", "fqid": "a/1"}]
    response = json_client.post(WRITE_URL, data)
    assert_response_code(response, 201)
    assert_model("a/1", {"f": 1}, 2)
    assert_modified_fields(redis_connection, {"a/1": ["f"]})


def test_restore_without_delete(json_client, data, redis_connection, reset_redis_data):
    response = json_client.post(WRITE_URL, data)
    assert_response_code(response, 201)
    assert_model("a/1", {"f": 1}, 1)
    assert_modified_fields(redis_connection, {"a/1": ["f"]})
    reset_redis_data()

    data["events"] = [{"type": "restore", "fqid": "a/1"}]
    response = json_client.post(WRITE_URL, data)
    assert_error_response(response, ERROR_CODES.MODEL_NOT_DELETED)
    assert_model("a/1", {"f": 1}, 1)
    assert_no_modified_fields(redis_connection)


def test_write_none(json_client, data, redis_connection, reset_redis_data):
    create_model(json_client, data, redis_connection, reset_redis_data)

    data["events"][0] = {"type": "update", "fqid": "a/1", "fields": {"f": None}}
    response = json_client.post(WRITE_URL, data)
    assert_response_code(response, 201)
    assert_model("a/1", {}, 2)
    assert_modified_fields(redis_connection, {"a/1": ["f"]}, meta_deleted=False)
