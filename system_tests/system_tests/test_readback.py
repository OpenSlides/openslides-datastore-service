import copy

import pytest
import requests

from datastore.reader.flask_frontend.routes import Route
from datastore.shared.flask_frontend import ERROR_CODES
from datastore.writer.flask_frontend.routes import WRITE_URL
from tests import assert_error_response, assert_response_code


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


def test_create_get(env, data):
    response = requests.post(
        env.writer + WRITE_URL,
        json=data,
    )
    assert_response_code(response, 201)

    response = requests.post(env.reader + Route.GET.URL, json={"fqid": "a/1"})
    assert response.json() == {
        "f": 1,
        "meta_deleted": False,
        "meta_position": 1,
    }


def test_create_delete_get(env, data):
    data["events"].append({"type": "delete", "fqid": "a/1"})
    response = requests.post(
        env.writer + WRITE_URL,
        json=data,
    )
    assert_response_code(response, 201)

    response = requests.post(env.reader + Route.GET.URL, json={"fqid": "a/1"})
    assert_error_response(response, ERROR_CODES.MODEL_DOES_NOT_EXIST)
