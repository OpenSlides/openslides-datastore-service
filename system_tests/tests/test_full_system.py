import pytest
import requests


WRITER_BASE_URL = "http://localhost:9011/internal/datastore/writer/"
WRITE_URL = WRITER_BASE_URL + "write"
TRUNCATE_DB_URL = WRITER_BASE_URL + "truncate_db"
READER_BASE_URL = "http://localhost:9010/internal/datastore/reader/"
GET_URL = READER_BASE_URL + "get"


@pytest.fixture(autouse=True)
def truncate_db():
    response = requests.post(TRUNCATE_DB_URL)
    assert response.status_code == 200
    yield


def test_create_get():
    response = requests.post(
        WRITE_URL,
        json={
            "user_id": 1,
            "information": {},
            "locked_fields": {},
            "events": [{"type": "create", "fqid": "a/1", "fields": {"f": 1}}],
        },
    )
    assert response.status_code == 201
    response = requests.post(GET_URL, json={"fqid": "a/1"})
    assert response.json() == {
        "f": 1,
        "meta_deleted": False,
        "meta_position": 1,
    }
