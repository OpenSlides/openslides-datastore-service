import copy

import pytest

from datastore.writer.flask_frontend.routes import RESERVE_IDS_URL, WRITE_URL
from tests.util import assert_response_code


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


def test_create_reserve(json_client, data, db_cur):
    response = json_client.post(WRITE_URL, data)
    assert_response_code(response, 201)

    response = json_client.post(RESERVE_IDS_URL, {"amount": 1, "collection": "a"})
    assert response.status_code == 200

    assert response.json == {"ids": [2]}

    db_cur.execute("select * from id_sequences")
    result = db_cur.fetchall()
    assert result == [("a", 3)]


def test_reserve_create(json_client, data, db_cur):
    response = json_client.post(RESERVE_IDS_URL, {"amount": 5, "collection": "a"})
    assert_response_code(response, 200)
    assert response.json == {"ids": [1, 2, 3, 4, 5]}

    db_cur.execute("select * from id_sequences")
    result = db_cur.fetchall()
    assert result == [("a", 6)]

    response = json_client.post(WRITE_URL, data)
    assert_response_code(response, 201)

    db_cur.execute("select * from id_sequences")
    result = db_cur.fetchall()
    assert result == [("a", 6)]
