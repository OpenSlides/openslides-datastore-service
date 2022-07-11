import copy

import pytest

from datastore.shared.flask_frontend import ERROR_CODES
from datastore.writer.flask_frontend.routes import WRITE_URL
from tests.util import assert_error_response, assert_response_code
from tests.writer.system.util import assert_model, assert_no_model


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


def _set_model(json_client, fqid, payload, mode):
    response = json_client.post(
        WRITE_URL,
        {
            "user_id": 1,
            "information": {},
            "locked_fields": {},
            "events": [{"type": mode, "fqid": fqid, "fields": payload}],
        },
    )
    assert_response_code(response, 201)


def create_model(json_client, fqid, payload):
    _set_model(json_client, fqid, payload, "create")


def update_model(json_client, fqid, payload):
    _set_model(json_client, fqid, payload, "update")


def create_and_update_model(json_client, fqid, create_payload, update_payload):
    create_model(json_client, fqid, create_payload)
    update_model(json_client, fqid, update_payload)


# FQIDs


def test_lock_fqid_ok(json_client, data):
    create_and_update_model(json_client, "a/1", {"f1": 1}, {"f2": 2})
    data["locked_fields"]["a/1"] = 2

    response = json_client.post(WRITE_URL, data)
    assert_response_code(response, 201)
    assert_model("a/2", {}, 3)


def test_lock_not_existing_fqid(json_client, data):
    data["locked_fields"]["b/2"] = 1

    response = json_client.post(WRITE_URL, data)
    assert_response_code(response, 201)
    assert_model("a/2", {}, 1)


def test_lock_fqid_not_ok(json_client, data):
    create_and_update_model(json_client, "a/1", {"f1": 1}, {"f2": 2})
    data["locked_fields"]["a/1"] = 1

    response = json_client.post(WRITE_URL, data)
    assert_error_response(response, ERROR_CODES.MODEL_LOCKED)
    assert response.json["error"]["keys"] == ["a/1"]
    assert_no_model("a/2")


# FQFields


def test_lock_fqfield_ok_1(json_client, data):
    create_and_update_model(json_client, "a/1", {"f1": 1}, {"f2": 2})
    data["locked_fields"]["a/1/f1"] = 1

    response = json_client.post(WRITE_URL, data)
    assert_response_code(response, 201)
    assert_model("a/2", {}, 3)


def test_lock_fqfield_ok_2(json_client, data):
    create_and_update_model(json_client, "a/1", {"f1": 1}, {"f2": 2})
    data["locked_fields"]["a/1/f2"] = 2

    response = json_client.post(WRITE_URL, data)
    assert_response_code(response, 201)
    assert_model("a/2", {}, 3)


def test_lock_not_existing_fqfield(json_client, data):
    data["locked_fields"]["b/2/f1"] = 1

    response = json_client.post(WRITE_URL, data)
    assert_response_code(response, 201)
    assert_model("a/2", {}, 1)


def test_lock_fqfield_not_ok(json_client, data):
    create_and_update_model(json_client, "a/1", {"f1": 1}, {"f2": 2})
    data["locked_fields"]["a/1/f2"] = 1

    response = json_client.post(WRITE_URL, data)
    assert_error_response(response, ERROR_CODES.MODEL_LOCKED)
    assert response.json["error"]["keys"] == ["a/1/f2"]
    assert_no_model("a/2")


# Collectionfields


def test_lock_collectionfield_ok_1(json_client, data):
    create_and_update_model(json_client, "a/1", {"f1": 1}, {"f2": 2})
    data["locked_fields"]["a/f1"] = 1

    response = json_client.post(WRITE_URL, data)
    assert_response_code(response, 201)
    assert_model("a/2", {}, 3)


def test_lock_collectionfield_ok_2(json_client, data):
    create_and_update_model(json_client, "a/1", {"f1": 1}, {"f2": 2})
    data["locked_fields"]["a/f2"] = 2

    response = json_client.post(WRITE_URL, data)
    assert_response_code(response, 201)
    assert_model("a/2", {}, 3)


def test_lock_not_existing_collectionfield(json_client, data):
    data["locked_fields"]["b/f1"] = 1

    response = json_client.post(WRITE_URL, data)
    assert_response_code(response, 201)
    assert_model("a/2", {}, 1)


def test_lock_collectionfield_not_ok(json_client, data):
    create_and_update_model(json_client, "a/1", {"f1": 1}, {"f2": 2})
    data["locked_fields"]["a/f2"] = 1

    response = json_client.post(WRITE_URL, data)
    assert_error_response(response, ERROR_CODES.MODEL_LOCKED)
    assert response.json["error"]["keys"] == ["a/f2"]
    assert_no_model("a/2")


# Collectionfields with filters


def test_lock_collectionfield_with_filter_ok(json_client, data):
    create_and_update_model(json_client, "a/1", {"f1": 1}, {"f2": 2})
    data["locked_fields"]["a/f1"] = {
        "position": 1,
        "filter": {
            "field": "f1",
            "operator": "=",
            "value": 1,
        },
    }

    response = json_client.post(WRITE_URL, data)
    assert_response_code(response, 201)
    assert_model("a/2", {}, 3)


def test_lock_collectionfield_with_filter_not_ok(json_client, data):
    create_and_update_model(json_client, "a/1", {"f1": 1}, {"f2": 2})
    data["locked_fields"]["a/f2"] = {
        "position": 1,
        "filter": {
            "field": "f1",
            "operator": "=",
            "value": 1,
        },
    }

    response = json_client.post(WRITE_URL, data)
    assert_error_response(response, ERROR_CODES.MODEL_LOCKED)
    assert_no_model("a/2")


def test_lock_collectionfield_with_filter_not_matching(json_client, data):
    create_and_update_model(json_client, "a/1", {"f1": 1}, {"f2": 2})
    data["locked_fields"]["a/f2"] = {
        "position": 1,
        "filter": {
            "field": "f1",
            "operator": "=",
            "value": 2,
        },
    }

    response = json_client.post(WRITE_URL, data)
    assert_response_code(response, 201)
    assert_model("a/2", {}, 3)


def test_lock_collectionfield_mixed_ok(json_client, data):
    create_and_update_model(json_client, "a/1", {"f1": 1}, {"f2": 2})
    data["locked_fields"]["a/f1"] = {
        "position": 1,
        "filter": {
            "field": "f1",
            "operator": "=",
            "value": 1,
        },
    }
    data["locked_fields"]["a/f2"] = 2

    response = json_client.post(WRITE_URL, data)
    assert_response_code(response, 201)
    assert_model("a/2", {}, 3)


def test_lock_collectionfield_mixed_not_ok_1(json_client, data):
    create_and_update_model(json_client, "a/1", {"f1": 1}, {"f1": 2, "f2": 2})
    data["locked_fields"]["a/f1"] = {
        "position": 1,
        "filter": {
            "field": "f1",
            "operator": "=",
            "value": 2,
        },
    }
    data["locked_fields"]["a/f2"] = 2

    response = json_client.post(WRITE_URL, data)
    assert_error_response(response, ERROR_CODES.MODEL_LOCKED)
    assert_no_model("a/2")


def test_lock_collectionfield_mixed_not_ok_2(json_client, data):
    create_and_update_model(json_client, "a/1", {"f1": 1}, {"f1": 2, "f2": 2})
    data["locked_fields"]["a/f1"] = {
        "position": 2,
        "filter": {
            "field": "f1",
            "operator": "=",
            "value": 2,
        },
    }
    data["locked_fields"]["a/f2"] = 1

    response = json_client.post(WRITE_URL, data)
    assert_error_response(response, ERROR_CODES.MODEL_LOCKED)
    assert_no_model("a/2")


def test_lock_collectionfield_prefix_not_locked(json_client, data):
    create_and_update_model(json_client, "a_suf/1", {"f1": 1}, {"f1": 2, "f2": 2})
    data["locked_fields"]["a/f1"] = {
        "position": 1,
        "filter": {
            "field": "f1",
            "operator": "=",
            "value": 2,
        },
    }

    response = json_client.post(WRITE_URL, data)
    assert_response_code(response, 201)
    assert_model("a/2", {}, 3)


def test_lock_collectionfield_with_and_filter(json_client, data):
    create_and_update_model(json_client, "a/1", {"f1": 1, "f3": False}, {"f2": 2})
    data["locked_fields"]["a/f1"] = {
        "position": 1,
        "filter": {
            "and_filter": [
                {
                    "field": "f1",
                    "operator": "=",
                    "value": 1,
                },
                {
                    "field": "f3",
                    "operator": "=",
                    "value": False,
                },
            ],
        },
    }
    response = json_client.post(WRITE_URL, data)
    assert_response_code(response, 201)
    assert_model("a/2", {}, 3)


def test_lock_collectionfield_empty_array(json_client, data):
    create_and_update_model(json_client, "a/1", {"f1": 1, "f3": False}, {"f2": 2})
    data["locked_fields"]["a/f1"] = []
    response = json_client.post(WRITE_URL, data)
    assert_response_code(response, 400)


def test_lock_collectionfield_multiple_locks_ok(json_client, data):
    create_and_update_model(json_client, "a/1", {"f1": 1}, {"f2": 2})
    data["locked_fields"]["a/f1"] = [
        {
            "position": 1,
            "filter": {
                "field": "f1",
                "operator": "=",
                "value": 1,
            },
        },
        {
            "position": 1,
            "filter": {
                "field": "f2",
                "operator": "=",
                "value": 2,
            },
        },
    ]

    response = json_client.post(WRITE_URL, data)
    assert_response_code(response, 201)
    assert_model("a/2", {}, 3)


def test_lock_collectionfield_multiple_locks_not_ok(json_client, data):
    create_and_update_model(json_client, "a/1", {"f1": 1}, {"f2": 2})
    data["locked_fields"]["a/f2"] = [
        {
            "position": 1,
            "filter": {
                "field": "f1",
                "operator": "=",
                "value": 1,
            },
        },
        {
            "position": 2,
            "filter": {
                "field": "f2",
                "operator": "=",
                "value": 2,
            },
        },
    ]

    response = json_client.post(WRITE_URL, data)
    assert_error_response(response, ERROR_CODES.MODEL_LOCKED)
    assert_no_model("a/2")


# Template fields


def test_lock_fqfield_template_with_suffix_locked(json_client, data):
    create_and_update_model(
        json_client, "a/1", {"f_$1_s": 1, "f_$_s": ["1"]}, {"f_$1_s": 2, "f_$_s": ["2"]}
    )
    data["locked_fields"]["a/1/f_$_s"] = 1

    response = json_client.post(WRITE_URL, data)
    assert_error_response(response, ERROR_CODES.MODEL_LOCKED)
    assert_no_model("a/2")


def test_lock_fqfield_template_dollar_sign(json_client, data):
    create_and_update_model(json_client, "a/1", {"f_$_s": 1}, {"f_$_s": 2})
    data["locked_fields"]["a/1/f_$_s"] = 1

    response = json_client.post(WRITE_URL, data)
    assert_error_response(response, ERROR_CODES.MODEL_LOCKED)
    assert_no_model("a/2")


def test_lock_fqfield_template_two_placeholders(json_client, data):
    create_and_update_model(json_client, "a/1", {"f_1_2_s": 1}, {"f_1_2_s": 2})
    data["locked_fields"]["a/1/f_$_$_s"] = 1

    response = json_client.post(WRITE_URL, data)
    assert_error_response(response, ERROR_CODES.INVALID_FORMAT)
    assert_no_model("a/2")


def test_lock_fqfield_template_empty_placeholder(json_client, data):
    create_and_update_model(json_client, "a/1", {"f__s": 1}, {"f__s": 2})
    data["locked_fields"]["a/1/f_$_s"] = 1

    response = json_client.post(WRITE_URL, data)
    assert_response_code(response, 201)
    assert_model("a/2", {}, 3)


def test_lock_fqfield_template_other_field_locked(json_client, data):
    create_and_update_model(json_client, "a/1", {"f_$1": 1}, {"f_$1": 2})
    data["locked_fields"]["a/1/f_$2"] = 1

    response = json_client.post(WRITE_URL, data)
    assert_response_code(response, 201)
    assert_model("a/2", {}, 3)


def test_lock_fqfield_template_other_field_locked_2(json_client, data):
    create_and_update_model(json_client, "a/1", {"f_$1": 1}, {"f_$1": 2})
    data["locked_fields"]["a/1/f_$11"] = 1

    response = json_client.post(WRITE_URL, data)
    assert_response_code(response, 201)
    assert_model("a/2", {}, 3)


def test_lock_fqfield_template_other_field_locked_3(json_client, data):
    create_and_update_model(json_client, "a/1", {"f_$11": 1}, {"f_$11": 2})
    data["locked_fields"]["a/1/f_$1"] = 1

    response = json_client.post(WRITE_URL, data)
    assert_response_code(response, 201)
    assert_model("a/2", {}, 3)


def test_lock_fqfield_template_template_field_locked(json_client, data):
    create_and_update_model(
        json_client, "a/1", {"f_$1": 1, "f_$": ["1"]}, {"f_$1": 2, "f_$": ["2"]}
    )
    data["locked_fields"]["a/1/f_$"] = 1

    response = json_client.post(WRITE_URL, data)
    assert_error_response(response, ERROR_CODES.MODEL_LOCKED)
    assert_no_model("a/2")


def test_lock_fqfield_template_same_field_locked(json_client, data):
    create_and_update_model(json_client, "a/1", {"f_$1": 1}, {"f_$1": 2})
    data["locked_fields"]["a/1/f_$1"] = 1

    response = json_client.post(WRITE_URL, data)
    assert_error_response(response, ERROR_CODES.MODEL_LOCKED)
    assert_no_model("a/2")


def test_lock_fqfield_template_other_field_with_suffix_locked(json_client, data):
    create_and_update_model(json_client, "a/1", {"f_$1_s": 1}, {"f_$1_s": 2})
    data["locked_fields"]["a/1/f_$2_s"] = 1

    response = json_client.post(WRITE_URL, data)
    assert_response_code(response, 201)
    assert_model("a/2", {}, 3)


def test_lock_fqfield_template_other_field_with_suffix_locked_2(json_client, data):
    create_and_update_model(json_client, "a/1", {"f_$1_s": 1}, {"f_$1_s": 2})
    data["locked_fields"]["a/1/f_$11_s"] = 1

    response = json_client.post(WRITE_URL, data)
    assert_response_code(response, 201)
    assert_model("a/2", {}, 3)


def test_lock_fqfield_template_other_field_with_suffix_locked_3(json_client, data):
    create_and_update_model(json_client, "a/1", {"f_$11_s": 1}, {"f_$11_s": 2})
    data["locked_fields"]["a/1/f_$1_s"] = 1

    response = json_client.post(WRITE_URL, data)
    assert_response_code(response, 201)
    assert_model("a/2", {}, 3)


def test_lock_fqfield_template_same_field_with_suffix_locked(json_client, data):
    create_and_update_model(json_client, "a/1", {"f_$1_s": 1}, {"f_$1_s": 2})
    data["locked_fields"]["a/1/f_$1_s"] = 1

    response = json_client.post(WRITE_URL, data)
    assert_error_response(response, ERROR_CODES.MODEL_LOCKED)
    assert_no_model("a/2")
