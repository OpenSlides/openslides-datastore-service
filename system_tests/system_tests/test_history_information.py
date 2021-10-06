import pytest
import requests
from datastore.reader.flask_frontend.routes import Route
from datastore.writer.flask_frontend.routes import WRITE_URL

from tests import assert_response_code


@pytest.fixture()
def write(env):
    def _write(user_id, information, event):
        response = requests.post(
            env.writer + WRITE_URL,
            json={
                "user_id": user_id,
                "information": information,
                "locked_fields": {},
                "events": [event],
            },
        )
        assert_response_code(response, 201)

    yield _write


def remove_timestamps(response):
    for information in response.values():
        for position in information:
            del position["timestamp"]


def test_simple(write, env):
    write(2, ["created1"], {"type": "create", "fqid": "a/1", "fields": {"f": 1}})
    write(3, ["updated1"], {"type": "update", "fqid": "a/1", "fields": {"f": 2}})
    write(4, ["created2"], {"type": "create", "fqid": "a/2", "fields": {"f": 1}})
    write(5, ["deleted1"], {"type": "delete", "fqid": "a/1"})

    response = requests.post(
        env.reader + Route.HISTORY_INFORMATION.URL, json={"fqids": ["a/1"]}
    ).json()
    remove_timestamps(response)
    assert response == {
        "a/1": [
            {
                "position": 1,
                "user_id": 2,
                "information": ["created1"],
            },
            {
                "position": 2,
                "user_id": 3,
                "information": ["updated1"],
            },
            {
                "position": 4,
                "user_id": 5,
                "information": ["deleted1"],
            },
        ]
    }


def test_omit_empty(write, env):
    write(2, [], {"type": "create", "fqid": "a/1", "fields": {"f": 1}})
    write(
        3,
        ["something important"],
        {"type": "update", "fqid": "a/1", "fields": {"f": 2}},
    )
    write(4, {}, {"type": "update", "fqid": "a/1", "fields": {"f": 3}})
    write(5, None, {"type": "update", "fqid": "a/1", "fields": {"f": 4}})

    response = requests.post(
        env.reader + Route.HISTORY_INFORMATION.URL, json={"fqids": ["a/1"]}
    ).json()
    remove_timestamps(response)
    assert response == {
        "a/1": [
            {
                "position": 2,
                "user_id": 3,
                "information": ["something important"],
            }
        ]
    }


def test_multiple_models(write, env):
    write(2, ["created a/1"], {"type": "create", "fqid": "a/1", "fields": {}})
    write(2, ["created a/2"], {"type": "create", "fqid": "a/2", "fields": {}})
    write(2, ["created a/3"], {"type": "create", "fqid": "a/3", "fields": {}})

    response = requests.post(
        env.reader + Route.HISTORY_INFORMATION.URL,
        json={"fqids": ["a/1", "a/3", "doesnotexist/1"]},
    ).json()
    remove_timestamps(response)
    assert response == {
        "a/1": [
            {
                "position": 1,
                "user_id": 2,
                "information": ["created a/1"],
            }
        ],
        "a/3": [
            {
                "position": 3,
                "user_id": 2,
                "information": ["created a/3"],
            }
        ],
    }
