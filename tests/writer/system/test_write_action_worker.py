import copy

import pytest

from datastore.writer.flask_frontend.routes import WRITE_ACTION_WORKER_URL
from tests.util import assert_response_code


@pytest.fixture()
def data():
    yield copy.deepcopy(
        [
            {
                "events": [
                    {
                        "type": "create",
                        "fqid": "action_worker/1",
                        "fields": {
                            "id": 1,
                            "name": "motion.create",
                            "state": "running",
                            "created": 1658489433,
                            "timestamp": 1658489434,
                        },
                    }
                ],
                "information": {"action_worker/1": ["create action_worker"]},
                "user_id": 1,
                "locked_fields": {},
            }
        ]
    )


def test_create_update_action_worker(json_client, data, db_cur):
    response = json_client.post(WRITE_ACTION_WORKER_URL, data)
    assert_response_code(response, 201)

    db_cur.execute("select fqid, data from models where fqid = 'action_worker/1'")
    fqid, result = db_cur.fetchone()
    assert fqid == "action_worker/1"
    assert result["name"] == "motion.create"
    assert result["state"] == "running"

    data[0]["events"][0]["type"] = "update"
    data[0]["events"][0]["fields"] = {
        "state": "end",
        "timestamp": 1658489444,
        "response": "response depending",
    }
    response = json_client.post(WRITE_ACTION_WORKER_URL, data)
    assert_response_code(response, 200)
    db_cur.execute("select fqid, data from models where fqid = 'action_worker/1'")
    fqid, result = db_cur.fetchone()
    assert fqid == "action_worker/1"
    assert result["name"] == "motion.create"
    assert result["state"] == "end"


def test_create_action_worker_not_single_event(json_client, data, db_cur):
    data[0]["events"].append(
        {
            "type": "create",
            "fqid": "action_worker/2",
            "fields": {
                "id": 1,
                "name": "motion.create",
                "state": "running",
                "created": 1658489433,
                "timestamp": 1658489434,
            },
        }
    )
    response = json_client.post(WRITE_ACTION_WORKER_URL, data)
    assert_response_code(response, 400)
    assert (
        response.json["error"]["msg"] == "write_action_worker may contain only 1 event!"
    )


def test_create_action_worker_wrong_collection(json_client, data, db_cur):
    data[0]["events"][0]["fqid"] = "topic/1"
    response = json_client.post(WRITE_ACTION_WORKER_URL, data)
    assert_response_code(response, 400)
    assert (
        response.json["error"]["msg"]
        == "Collection for write_action_worker must be action_worker"
    )
