import copy

import pytest

from shared.util import META_FIELD_PREFIX
from tests.system.shared import WRITE_URL, assert_error_response, assert_no_db_entry
from writer.flask_frontend.routes import ERROR_CODES


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


@pytest.fixture(autouse=True)
def check_no_db_entry(db_cur):
    yield
    assert_no_db_entry(db_cur)


def test_wrong_format(json_client):
    response = json_client.post(WRITE_URL, ["not_valid", None])
    assert_error_response(response, ERROR_CODES.INVALID_REQUEST)


def test_no_json(client):
    response = client.post(WRITE_URL, data={"some": "data"})
    assert response.is_json
    assert_error_response(response, ERROR_CODES.INVALID_REQUEST)


def test_missing_user_id(json_client, data):
    del data["user_id"]
    response = json_client.post(WRITE_URL, data)
    assert_error_response(response, ERROR_CODES.INVALID_REQUEST)


def test_missing_information(json_client, data):
    del data["information"]
    response = json_client.post(WRITE_URL, data)
    assert_error_response(response, ERROR_CODES.INVALID_REQUEST)


def test_missing_locked_fields(json_client, data):
    del data["locked_fields"]
    response = json_client.post(WRITE_URL, data)
    assert_error_response(response, ERROR_CODES.INVALID_REQUEST)


def test_missing_events(json_client, data):
    del data["events"]
    response = json_client.post(WRITE_URL, data)
    assert_error_response(response, ERROR_CODES.INVALID_REQUEST)


def test_empty_events(json_client, data):
    data["events"] = []
    response = json_client.post(WRITE_URL, data)
    assert_error_response(response, ERROR_CODES.INVALID_FORMAT)


def test_unknwon_event(json_client, data):
    data["events"][0]["type"] = "unknown"
    response = json_client.post(WRITE_URL, data)
    assert_error_response(response, ERROR_CODES.INVALID_REQUEST)


def test_missing_fqid(json_client, data):
    del data["events"][0]["fqid"]
    response = json_client.post(WRITE_URL, data)
    assert_error_response(response, ERROR_CODES.INVALID_REQUEST)


def test_create_invalid_fqid(json_client, data):
    data["events"][0]["fqid"] = "not valid"
    response = json_client.post(WRITE_URL, data)
    assert_error_response(response, ERROR_CODES.INVALID_FORMAT)


def test_create_missing_fields(json_client, data):
    del data["events"][0]["fields"]
    response = json_client.post(WRITE_URL, data)
    assert_error_response(response, ERROR_CODES.INVALID_REQUEST)


def test_create_invalid_field(json_client, data):
    data["events"][0]["fields"] = {META_FIELD_PREFIX: "value"}
    response = json_client.post(WRITE_URL, data)
    assert_error_response(response, ERROR_CODES.INVALID_FORMAT)


def test_update_empty_fields(json_client, data):
    data["events"][0]["fields"] = {}
    data["events"][0]["type"] = "update"
    response = json_client.post(WRITE_URL, data)
    assert_error_response(response, ERROR_CODES.INVALID_FORMAT)


def test_update_missing_fields(json_client, data):
    del data["events"][0]["fields"]
    data["events"][0]["type"] = "update"
    response = json_client.post(WRITE_URL, data)
    assert_error_response(response, ERROR_CODES.INVALID_REQUEST)


def test_update_invalid_field(json_client, data):
    data["events"][0]["fields"] = {META_FIELD_PREFIX: "value"}
    data["events"][0]["type"] = "update"
    response = json_client.post(WRITE_URL, data)
    assert_error_response(response, ERROR_CODES.INVALID_FORMAT)


def test_locked_fields_invalid_key(json_client, data):
    for key in ("collection", "_collection/field", "c/c/f", "1/1/1"):
        data["locked_fields"] = {key: 1}

        response = json_client.post(WRITE_URL, data)
        assert_error_response(response, ERROR_CODES.INVALID_FORMAT)


def test_lock_negative_position(json_client, data):
    data["locked_fields"]["a/1"] = -1

    response = json_client.post(WRITE_URL, data)
    assert_error_response(response, ERROR_CODES.INVALID_FORMAT)


def test_lock_null_position(json_client, data):
    data["locked_fields"]["a/1"] = 0

    response = json_client.post(WRITE_URL, data)
    assert_error_response(response, ERROR_CODES.INVALID_FORMAT)
