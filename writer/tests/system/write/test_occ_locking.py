import copy

import pytest

from shared.flask_frontend import ERROR_CODES
from shared.tests.util import assert_error_response
from tests.system.util import WRITE_URL, assert_model, assert_no_model


@pytest.fixture()
def data():
    yield copy.deepcopy(
        {
            "user_id": 1,
            "information": {},
            "locked_fields": {},
            "events": [{"type": "create", "fqid": "a/2", "fields": {}}],
        }
    )


def create_and_update_model(json_client, fqid, create_payload, update_payload):
    response = json_client.post(
        WRITE_URL,
        {
            "user_id": 1,
            "information": {},
            "locked_fields": {},
            "events": [{"type": "create", "fqid": fqid, "fields": create_payload}],
        },
    )
    assert response.status_code == 200
    response = json_client.post(
        WRITE_URL,
        {
            "user_id": 1,
            "information": {},
            "locked_fields": {},
            "events": [{"type": "update", "fqid": fqid, "fields": update_payload}],
        },
    )
    assert response.status_code == 200


def test_lock_fqid_ok(json_client, data):
    create_and_update_model(json_client, "a/1", {"f1": 1}, {"f2": 2})
    data["locked_fields"]["a/1"] = 2

    response = json_client.post(WRITE_URL, data)
    assert response.status_code == 200
    assert_model("a/2", {}, 3)


def test_lock_not_existing_fqid(json_client, data):
    data["locked_fields"]["b/2"] = 1

    response = json_client.post(WRITE_URL, data)
    assert response.status_code == 200
    assert_model("a/2", {}, 1)


def test_lock_fqid_not_ok(json_client, data):
    create_and_update_model(json_client, "a/1", {"f1": 1}, {"f2": 2})
    data["locked_fields"]["a/1"] = 1

    response = json_client.post(WRITE_URL, data)
    assert_error_response(response, ERROR_CODES.MODEL_LOCKED)
    assert_no_model("a/2")


def test_lock_fqfield_ok_1(json_client, data):
    create_and_update_model(json_client, "a/1", {"f1": 1}, {"f2": 2})
    data["locked_fields"]["a/1/f1"] = 1

    response = json_client.post(WRITE_URL, data)
    assert response.status_code == 200
    assert_model("a/2", {}, 3)


def test_lock_fqfield_ok_2(json_client, data):
    create_and_update_model(json_client, "a/1", {"f1": 1}, {"f2": 2})
    data["locked_fields"]["a/1/f2"] = 2

    response = json_client.post(WRITE_URL, data)
    assert response.status_code == 200
    assert_model("a/2", {}, 3)


def test_lock_not_existing_fqfield(json_client, data):
    data["locked_fields"]["b/2/f1"] = 1

    response = json_client.post(WRITE_URL, data)
    assert response.status_code == 200
    assert_model("a/2", {}, 1)


def test_lock_fqfield_not_ok(json_client, data):
    create_and_update_model(json_client, "a/1", {"f1": 1}, {"f2": 2})
    data["locked_fields"]["a/1/f2"] = 1

    response = json_client.post(WRITE_URL, data)
    assert_error_response(response, ERROR_CODES.MODEL_LOCKED)
    assert_no_model("a/2")


def test_lock_collectionfield_ok_1(json_client, data):
    create_and_update_model(json_client, "a/1", {"f1": 1}, {"f2": 2})
    data["locked_fields"]["a/f1"] = 1

    response = json_client.post(WRITE_URL, data)
    assert response.status_code == 200
    assert_model("a/2", {}, 3)


def test_lock_collectionfield_ok_2(json_client, data):
    create_and_update_model(json_client, "a/1", {"f1": 1}, {"f2": 2})
    data["locked_fields"]["a/f2"] = 2

    response = json_client.post(WRITE_URL, data)
    assert response.status_code == 200
    assert_model("a/2", {}, 3)


def test_lock_not_existing_collectionfield(json_client, data):
    data["locked_fields"]["b/f1"] = 1

    response = json_client.post(WRITE_URL, data)
    assert response.status_code == 200
    assert_model("a/2", {}, 1)


def test_lock_collectionfield_not_ok(json_client, data):
    create_and_update_model(json_client, "a/1", {"f1": 1}, {"f2": 2})
    data["locked_fields"]["a/f2"] = 1

    response = json_client.post(WRITE_URL, data)
    assert_error_response(response, ERROR_CODES.MODEL_LOCKED)
    assert_no_model("a/2")
