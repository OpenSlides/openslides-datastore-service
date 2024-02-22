import copy
from threading import Thread

import pytest
from datastore.writer.core.writer_service import WriterService

from datastore.writer.flask_frontend.routes import WRITE_URL, WRITE_WITHOUT_EVENTS_URL
from tests.util import assert_response_code
from datastore.shared.di import injector
from datastore.writer.core import Writer


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
                "information": {},
                "user_id": 1,
                "locked_fields": {},
            }
        ]
    )


def test_create_update_action_worker(json_client, data, db_cur):
    # create action_worker
    response = json_client.post(WRITE_WITHOUT_EVENTS_URL, data)
    assert_response_code(response, 201)

    db_cur.execute("select fqid, data from models where fqid = 'action_worker/1'")
    fqid, result = db_cur.fetchone()
    assert fqid == "action_worker/1"
    assert result["name"] == "motion.create"
    assert result["state"] == "running"

    data_single = data[0]
    # update timestamp of action worker
    data_single["events"][0]["type"] = "update"
    data_single["events"][0]["fields"] = {
        "timestamp": 1658489444,
    }
    response = json_client.post(WRITE_WITHOUT_EVENTS_URL, data)
    assert_response_code(response, 201)
    db_cur.execute("select fqid, data from models where fqid = 'action_worker/1'")
    fqid, result = db_cur.fetchone()
    assert fqid == "action_worker/1"
    assert result["name"] == "motion.create"
    assert result["state"] == "running"

    # end action_worker
    data_single["events"][0]["fields"] = {
        "state": "end",
        "timestamp": 1658489454,
    }
    response = json_client.post(WRITE_WITHOUT_EVENTS_URL, data)
    assert_response_code(response, 201)
    db_cur.execute("select fqid, data from models where fqid = 'action_worker/1'")
    fqid, result = db_cur.fetchone()
    assert fqid == "action_worker/1"
    assert result["name"] == "motion.create"
    assert result["state"] == "end"


def test_create_action_worker_not_single_event(json_client, data, db_cur):
    data_single = data[0]
    data_single["events"].append(
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
    response = json_client.post(WRITE_WITHOUT_EVENTS_URL, data)
    assert_response_code(response, 400)
    assert (
        response.json["error"]["msg"]
        == "write_without_events may contain only 1 event!"
    )


def test_create_action_worker_data_not_in_list_format(json_client, data, db_cur):
    data_single = data[0]
    response = json_client.post(WRITE_WITHOUT_EVENTS_URL, data_single)
    assert_response_code(response, 400)
    assert (
        response.json["error"]["msg"]
        == "write_without_events data internally must be a list!"
    )


def test_create_action_worker_wrong_collection(json_client, data, db_cur):
    data_single = data[0]
    data_single["events"][0]["fqid"] = "topic/1"
    response = json_client.post(WRITE_WITHOUT_EVENTS_URL, data)
    assert_response_code(response, 400)
    assert (
        response.json["error"]["msg"]
        == "Collection for write_without_events must be action_worker or import_preview"
    )


def test_delete_action_worker_wrong_collection(json_client, data, db_cur):
    data = [
        {
            "events": [{"type": "delete", "fqid": "topic/1"}],
            "user_id": 1,
            "locked_fields": {},
        }
    ]

    response = json_client.post(WRITE_WITHOUT_EVENTS_URL, data)
    assert_response_code(response, 400)
    assert (
        response.json["error"]["msg"]
        == "Collection for write_without_events must be action_worker or import_preview"
    )


def test_delete_action_worker_with_2_events(json_client, data, db_cur):
    db_cur.execute(
        "insert into models (fqid, data, deleted) values"
        " ('action_worker/1', '{\"data\": \"content1\"}', false),"
        " ('action_worker/2', '{\"data\": \"content2\"}', false);"
    )
    db_cur.connection.commit()
    db_cur.execute(
        "select fqid from models where fqid in ('action_worker/1', 'action_worker/2')"
    )
    result = db_cur.fetchall()
    assert len(result) == 2, "There must be 2 records found"

    data = [
        {
            "events": [
                {"type": "delete", "fqid": "action_worker/1"},
                {"type": "delete", "fqid": "action_worker/2"},
            ],
            "user_id": 1,
            "information": {},
            "locked_fields": {},
        }
    ]

    response = json_client.post(WRITE_WITHOUT_EVENTS_URL, data)
    assert_response_code(response, 200)
    db_cur.execute(
        "select fqid from models where fqid in ('action_worker/1', 'action_worker/2')"
    )
    result = db_cur.fetchall()
    assert len(result) == 0, "There must be 0 records found"


def test_write_action_worker_during_request(json_client, data, db_cur):
    response = json_client.post(WRITE_WITHOUT_EVENTS_URL, data)
    assert_response_code(response, 201)
    
    writer: WriterService = injector.get(Writer)
    writer._lock.acquire()

    thread = start_thread(json_client, [
        {
            "events": [
                {
                    "type": "create",
                    "fqid": "model/1",
                    "fields": {
                        "id": 1,
                    },
                }
            ],
            "information": {},
            "user_id": 1,
            "locked_fields": {},
        }
    ])
    thread.join(0.1)
    assert thread.is_alive()
    
    data[0]["events"][0]["type"] = "update"
    data[0]["events"][0]["fields"] = {"timestamp": 1658489444}
    response = json_client.post(WRITE_WITHOUT_EVENTS_URL, data)
    assert_response_code(response, 201)

    db_cur.execute("select data from models where fqid = 'model/1'")
    result = db_cur.fetchall()
    assert len(result) == 0

    db_cur.execute("select data->>'timestamp' from models where fqid = 'action_worker/1'")
    assert db_cur.fetchone() == ("1658489444",)

    writer._lock.release()
    thread.join(0.1)
    assert not thread.is_alive()

    db_cur.execute("select data from models where fqid = 'model/1'")
    result = db_cur.fetchall()
    assert len(result) == 1

def start_thread(json_client, payload):
    thread = Thread(
        target=json_client.post,
        args=[WRITE_URL, payload],
    )
    thread.start()
    return thread
