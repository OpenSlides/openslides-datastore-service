import copy

import pytest
import requests

from reader.flask_frontend.routes import Route
from shared.flask_frontend import ERROR_CODES
from shared.services import EnvironmentService
from shared.tests import assert_error_response, assert_response_code
from writer.flask_frontend.routes import (
    TRUNCATE_DB_URL as TRUNCATE_DB_URL_PATH,
    WRITE_URL as WRITE_URL_PATH,
)


env_service = EnvironmentService()

WRITER_PORT = env_service.get("OPENSLIDES_DATASTORE_WRITER_PORT")
READER_PORT = env_service.get("OPENSLIDES_DATASTORE_READER_PORT")

WRITER_HOST = f"http://localhost:{WRITER_PORT}"
READER_HOST = f"http://localhost:{READER_PORT}"

WRITE_URL = WRITER_HOST + WRITE_URL_PATH
TRUNCATE_DB_URL = WRITER_HOST + TRUNCATE_DB_URL_PATH

GET_URL = READER_HOST + Route.GET.URL


@pytest.fixture(autouse=True)
def truncate_db():
    response = requests.post(TRUNCATE_DB_URL)
    assert response.status_code == 200
    yield


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


def test_create_get(data):
    response = requests.post(WRITE_URL, json=data,)
    assert_response_code(response, 201)

    response = requests.post(GET_URL, json={"fqid": "a/1"})
    assert response.json() == {
        "f": 1,
        "meta_deleted": False,
        "meta_position": 1,
    }


def test_create_delete_get(data):
    data["events"].append({"type": "delete", "fqid": "a/1"})
    response = requests.post(WRITE_URL, json=data,)
    assert_response_code(response, 201)

    response = requests.post(GET_URL, json={"fqid": "a/1"})
    assert_error_response(response, ERROR_CODES.MODEL_DOES_NOT_EXIST)
