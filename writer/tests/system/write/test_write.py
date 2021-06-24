import copy
from unittest.mock import patch

import psycopg2
import pytest

from shared.di import injector
from shared.flask_frontend import ERROR_CODES
from shared.postgresql_backend import ConnectionHandler
from shared.services import ReadDatabase
from shared.tests.util import assert_error_response, assert_response_code
from shared.util import DeletedModelsBehaviour
from tests.system.util import (
    assert_model,
    assert_modified_fields,
    assert_no_db_entry,
    assert_no_model,
    assert_no_modified_fields,
)
from writer.core import Messaging
from writer.flask_frontend.routes import WRITE_URL


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


def create_model(json_client, data, redis_connection, reset_redis_data):
    fields = copy.deepcopy(data["events"][0]["fields"])
    response = json_client.post(WRITE_URL, data)
    assert_response_code(response, 201)
    assert_model("a/1", fields, 1)
    assert_modified_fields(redis_connection, {"a/1": list(fields.keys())})
    reset_redis_data()


def test_create_simple(json_client, data, redis_connection, reset_redis_data):
    create_model(json_client, data, redis_connection, reset_redis_data)


def test_assert_increased_id_sequence(
    json_client, data, redis_connection, reset_redis_data, db_cur
):
    create_model(json_client, data, redis_connection, reset_redis_data)
    db_cur.execute("select id from id_sequences where collection = %s", ["a"])
    id = db_cur.fetchone()[0]
    assert id == 2


def test_create_double_assert_increased_id_sequence(
    json_client, data, redis_connection, reset_redis_data, db_cur
):
    create_model(json_client, data, redis_connection, reset_redis_data)
    data["events"][0]["fqid"] = "a/3"
    response = json_client.post(WRITE_URL, data)
    assert_response_code(response, 201)
    db_cur.execute("select id from id_sequences where collection = %s", ["a"])
    id = db_cur.fetchone()[0]
    assert id == 4


def test_create_empty_field(json_client, data, redis_connection):
    data["events"][0]["fields"]["empty"] = None
    response = json_client.post(WRITE_URL, data)
    assert_response_code(response, 201)
    assert_model("a/1", {"f": 1}, 1)
    assert_modified_fields(redis_connection, {"a/1": ["f"]})


def test_create_twice(json_client, data, db_cur, redis_connection):
    data["events"].append(data["events"][0])
    response = json_client.post(WRITE_URL, data)
    assert_error_response(response, ERROR_CODES.MODEL_EXISTS)
    assert_no_db_entry(db_cur)
    assert_no_modified_fields(redis_connection)


def test_create_update(json_client, data, redis_connection):
    field_data = [True, None, {"test": "value"}]
    data["events"].append(
        {
            "type": "update",
            "fqid": "a/1",
            "fields": {"f": None, "another_field": field_data},
        }
    )
    response = json_client.post(WRITE_URL, data)
    assert_response_code(response, 201)
    assert_model("a/1", {"another_field": field_data}, 1)
    assert_modified_fields(redis_connection, {"a/1": ["f", "another_field"]})


def test_single_update(json_client, data, redis_connection, reset_redis_data):
    create_model(json_client, data, redis_connection, reset_redis_data)

    field_data = [True, None, {"test": "value"}]
    data["events"][0] = {
        "type": "update",
        "fqid": "a/1",
        "fields": {"f": None, "another_field": field_data},
    }
    response = json_client.post(WRITE_URL, data)
    assert_response_code(response, 201)
    assert_model("a/1", {"another_field": field_data}, 2)
    assert_modified_fields(
        redis_connection, {"a/1": ["f", "another_field"]}, meta_deleted=False
    )


def test_single_field_delete(json_client, data, redis_connection, reset_redis_data):
    create_model(json_client, data, redis_connection, reset_redis_data)

    data["events"][0] = {
        "type": "update",
        "fqid": "a/1",
        "fields": {"another_field": None},
    }
    response = json_client.post(WRITE_URL, data)
    assert_response_code(response, 201)
    assert_model("a/1", {"f": 1}, 2)
    assert_modified_fields(
        redis_connection, {"a/1": ["another_field"]}, meta_deleted=False
    )


def test_list_update_add_empty(json_client, data, redis_connection, reset_redis_data):
    create_model(json_client, data, redis_connection, reset_redis_data)

    data["events"][0] = {
        "type": "update",
        "fqid": "a/1",
        "list_fields": {"add": {"field": [1]}},
    }
    response = json_client.post(WRITE_URL, data)
    assert_response_code(response, 201)
    assert_model("a/1", {"f": 1, "field": [1]}, 2)
    assert_modified_fields(redis_connection, {"a/1": ["field"]}, meta_deleted=False)


def test_list_update_add_empty_2(json_client, data, redis_connection, reset_redis_data):
    data["events"][0]["fields"]["field"] = []
    create_model(json_client, data, redis_connection, reset_redis_data)

    data["events"][0] = {
        "type": "update",
        "fqid": "a/1",
        "list_fields": {"add": {"field": [1]}},
    }
    response = json_client.post(WRITE_URL, data)
    assert_response_code(response, 201)
    assert_model("a/1", {"f": 1, "field": [1]}, 2)
    assert_modified_fields(redis_connection, {"a/1": ["field"]}, meta_deleted=False)


def test_list_update_add_string(json_client, data, redis_connection, reset_redis_data):
    create_model(json_client, data, redis_connection, reset_redis_data)

    data["events"][0] = {
        "type": "update",
        "fqid": "a/1",
        "list_fields": {"add": {"field": ["str"]}},
    }
    response = json_client.post(WRITE_URL, data)
    assert_response_code(response, 201)
    assert_model("a/1", {"f": 1, "field": ["str"]}, 2)
    assert_modified_fields(redis_connection, {"a/1": ["field"]}, meta_deleted=False)


def test_list_update_add_existing(
    json_client, data, redis_connection, reset_redis_data
):
    data["events"][0]["fields"]["f"] = [42]
    create_model(json_client, data, redis_connection, reset_redis_data)

    data["events"][0] = {
        "type": "update",
        "fqid": "a/1",
        "list_fields": {"add": {"f": [1]}},
    }
    response = json_client.post(WRITE_URL, data)
    assert_response_code(response, 201)
    assert_model("a/1", {"f": [42, 1]}, 2)
    assert_modified_fields(redis_connection, {"a/1": ["f"]}, meta_deleted=False)


def test_list_update_add_no_array(
    json_client, data, redis_connection, reset_redis_data
):
    create_model(json_client, data, redis_connection, reset_redis_data)

    data["events"][0] = {
        "type": "update",
        "fqid": "a/1",
        "list_fields": {"add": {"f": [1]}},
    }
    response = json_client.post(WRITE_URL, data)
    assert_error_response(response, ERROR_CODES.INVALID_FORMAT)
    assert_model("a/1", {"f": 1}, 1)
    assert_no_modified_fields(redis_connection)


def test_list_update_add_invalid_entry(
    json_client, data, redis_connection, reset_redis_data
):
    data["events"][0]["fields"]["f"] = [[1]]
    create_model(json_client, data, redis_connection, reset_redis_data)

    data["events"][0] = {
        "type": "update",
        "fqid": "a/1",
        "list_fields": {"add": {"f": [1]}},
    }
    response = json_client.post(WRITE_URL, data)
    assert_error_response(response, ERROR_CODES.INVALID_FORMAT)
    assert_model("a/1", {"f": [[1]]}, 1)
    assert_no_modified_fields(redis_connection)


def test_list_update_add_duplicate(
    json_client, data, redis_connection, reset_redis_data
):
    data["events"][0]["fields"]["f"] = [1]
    create_model(json_client, data, redis_connection, reset_redis_data)

    data["events"][0] = {
        "type": "update",
        "fqid": "a/1",
        "list_fields": {"add": {"f": [1, 2]}},
    }
    response = json_client.post(WRITE_URL, data)
    assert_response_code(response, 201)
    assert_model("a/1", {"f": [1, 2]}, 2)
    assert_modified_fields(redis_connection, {"a/1": ["f"]}, meta_deleted=False)


def test_list_update_remove_empty_1(
    json_client, data, redis_connection, reset_redis_data
):
    create_model(json_client, data, redis_connection, reset_redis_data)

    data["events"][0] = {
        "type": "update",
        "fqid": "a/1",
        "list_fields": {"remove": {"field": [1]}},
    }
    response = json_client.post(WRITE_URL, data)
    assert_response_code(response, 201)
    assert_model("a/1", {"f": 1}, 2)
    assert_modified_fields(redis_connection, {"a/1": ["field"]}, meta_deleted=False)


def test_list_update_remove_empty_2(
    json_client, data, redis_connection, reset_redis_data
):
    data["events"][0]["fields"]["field"] = []
    create_model(json_client, data, redis_connection, reset_redis_data)

    data["events"][0] = {
        "type": "update",
        "fqid": "a/1",
        "list_fields": {"remove": {"field": [1]}},
    }
    response = json_client.post(WRITE_URL, data)
    assert_response_code(response, 201)
    assert_model("a/1", {"f": 1, "field": []}, 2)
    assert_modified_fields(redis_connection, {"a/1": ["field"]}, meta_deleted=False)


def test_list_update_remove_existing(
    json_client, data, redis_connection, reset_redis_data
):
    data["events"][0]["fields"]["f"] = [42]
    create_model(json_client, data, redis_connection, reset_redis_data)

    data["events"][0] = {
        "type": "update",
        "fqid": "a/1",
        "list_fields": {"remove": {"f": [42]}},
    }
    response = json_client.post(WRITE_URL, data)
    assert_response_code(response, 201)
    assert_model("a/1", {"f": []}, 2)
    assert_modified_fields(redis_connection, {"a/1": ["f"]}, meta_deleted=False)


def test_list_update_remove_no_array(
    json_client, data, redis_connection, reset_redis_data
):
    create_model(json_client, data, redis_connection, reset_redis_data)

    data["events"][0] = {
        "type": "update",
        "fqid": "a/1",
        "list_fields": {"remove": {"f": [1]}},
    }
    response = json_client.post(WRITE_URL, data)
    assert_error_response(response, ERROR_CODES.INVALID_FORMAT)
    assert_model("a/1", {"f": 1}, 1)
    assert_no_modified_fields(redis_connection)


def test_list_update_remove_invalid_entry(
    json_client, data, redis_connection, reset_redis_data
):
    data["events"][0]["fields"]["f"] = [[1]]
    create_model(json_client, data, redis_connection, reset_redis_data)

    data["events"][0] = {
        "type": "update",
        "fqid": "a/1",
        "list_fields": {"remove": {"f": [1]}},
    }
    response = json_client.post(WRITE_URL, data)
    assert_error_response(response, ERROR_CODES.INVALID_FORMAT)
    assert_model("a/1", {"f": [[1]]}, 1)
    assert_no_modified_fields(redis_connection)


def test_list_update_remove_not_existent(
    json_client, data, redis_connection, reset_redis_data
):
    data["events"][0]["fields"]["f"] = [1]
    create_model(json_client, data, redis_connection, reset_redis_data)

    data["events"][0] = {
        "type": "update",
        "fqid": "a/1",
        "list_fields": {"remove": {"f": [42]}},
    }
    response = json_client.post(WRITE_URL, data)
    assert_response_code(response, 201)
    assert_model("a/1", {"f": [1]}, 2)
    assert_modified_fields(redis_connection, {"a/1": ["f"]}, meta_deleted=False)


def test_list_update_remove_partially_not_existent(
    json_client, data, redis_connection, reset_redis_data
):
    data["events"][0]["fields"]["f"] = [1]
    create_model(json_client, data, redis_connection, reset_redis_data)

    data["events"][0] = {
        "type": "update",
        "fqid": "a/1",
        "list_fields": {"remove": {"f": [1, 42]}},
    }
    response = json_client.post(WRITE_URL, data)
    assert_response_code(response, 201)
    assert_model("a/1", {"f": []}, 2)
    assert_modified_fields(redis_connection, {"a/1": ["f"]}, meta_deleted=False)


def test_list_update_add_remove(json_client, data, redis_connection, reset_redis_data):
    data["events"][0]["fields"]["f"] = [1]
    data["events"][0]["fields"]["f2"] = ["test"]
    create_model(json_client, data, redis_connection, reset_redis_data)

    data["events"][0] = {
        "type": "update",
        "fqid": "a/1",
        "list_fields": {"add": {"f": [2]}, "remove": {"f2": ["test"]}},
    }
    response = json_client.post(WRITE_URL, data)
    assert_response_code(response, 201)
    assert_model("a/1", {"f": [1, 2], "f2": []}, 2)
    assert_modified_fields(redis_connection, {"a/1": ["f", "f2"]}, meta_deleted=False)


def test_list_update_add_remove_same_field(
    json_client, data, redis_connection, reset_redis_data
):
    data["events"][0]["fields"]["f"] = [1]
    create_model(json_client, data, redis_connection, reset_redis_data)

    data["events"][0] = {
        "type": "update",
        "fqid": "a/1",
        "list_fields": {"add": {"f": [2]}, "remove": {"f": [1]}},
    }
    response = json_client.post(WRITE_URL, data)
    assert_response_code(response, 201)
    assert_model("a/1", {"f": [2]}, 2)
    assert_modified_fields(redis_connection, {"a/1": ["f"]}, meta_deleted=False)


def test_update_and_list_update(json_client, data, redis_connection, reset_redis_data):
    data["events"][0]["fields"]["f"] = [1]
    create_model(json_client, data, redis_connection, reset_redis_data)

    data["events"][0] = {
        "type": "update",
        "fqid": "a/1",
        "fields": {"g": [2]},
        "list_fields": {"add": {"f": [2]}},
    }
    response = json_client.post(WRITE_URL, data)
    assert_response_code(response, 201)
    assert_model("a/1", {"f": [1, 2], "g": [2]}, 2)
    assert_modified_fields(redis_connection, {"a/1": ["f", "g"]}, meta_deleted=False)


def test_list_update_with_create(json_client, data, redis_connection, reset_redis_data):
    data["events"].append(
        {
            "type": "update",
            "fqid": "a/1",
            "list_fields": {"add": {"g": [2]}},
        }
    )
    response = json_client.post(WRITE_URL, data)
    assert_response_code(response, 201)
    assert_model("a/1", {"f": 1, "g": [2]}, 1)
    assert_modified_fields(redis_connection, {"a/1": ["f", "g"]})


def test_update_non_existing_1(json_client, data, db_cur, redis_connection):
    data["events"][0] = {"type": "update", "fqid": "a/1", "fields": {"f": "value"}}
    response = json_client.post(WRITE_URL, data)
    assert_error_response(response, ERROR_CODES.MODEL_DOES_NOT_EXIST)
    assert_no_db_entry(db_cur)
    assert_no_modified_fields(redis_connection)


def test_update_non_existing_2(json_client, data, db_cur, redis_connection):
    data["events"][0] = {"type": "update", "fqid": "a/1", "fields": {"f": None}}
    response = json_client.post(WRITE_URL, data)
    assert_error_response(response, ERROR_CODES.MODEL_DOES_NOT_EXIST)
    assert_no_db_entry(db_cur)
    assert_no_modified_fields(redis_connection)


def test_create_delete(json_client, data, redis_connection, reset_redis_data):
    data["events"].append({"type": "delete", "fqid": "a/1"})
    response = json_client.post(WRITE_URL, data)
    assert_response_code(response, 201)
    assert_no_model("a/1")
    assert_modified_fields(redis_connection, {"a/1": ["f"]})


def test_single_delete(json_client, data, redis_connection, reset_redis_data):
    create_model(json_client, data, redis_connection, reset_redis_data)

    data["events"][0] = {"type": "delete", "fqid": "a/1"}
    response = json_client.post(WRITE_URL, data)
    assert_response_code(response, 201)
    assert_no_model("a/1")

    # assert the model is still in the lookup table, but marked as deleted
    connection_handler = injector.get(ConnectionHandler)
    with connection_handler.get_connection_context():
        # read from read db
        read_db: ReadDatabase = injector.get(ReadDatabase)
        model = read_db.get("a/1", [], DeletedModelsBehaviour.ONLY_DELETED)
        assert model == {"f": 1, "meta_deleted": True, "meta_position": 2}
        assert read_db.is_deleted("a/1")

    assert_modified_fields(redis_connection, {"a/1": ["f"]})


def test_delete_model_does_not_exist(
    json_client, data, redis_connection, reset_redis_data
):
    data["events"][0] = {"type": "delete", "fqid": "a/1"}
    response = json_client.post(WRITE_URL, data)
    assert_error_response(response, ERROR_CODES.MODEL_DOES_NOT_EXIST)
    assert_no_model("a/1")
    assert_no_modified_fields(redis_connection)


def test_create_delete_restore(json_client, data, redis_connection):
    data["events"].append({"type": "delete", "fqid": "a/1"})
    data["events"].append({"type": "restore", "fqid": "a/1"})
    response = json_client.post(WRITE_URL, data)
    assert_response_code(response, 201)
    assert_model("a/1", {"f": 1}, 1)
    assert_modified_fields(redis_connection, {"a/1": ["f"]})


def test_single_restore(json_client, data, redis_connection, reset_redis_data):
    data["events"].append({"type": "delete", "fqid": "a/1"})
    response = json_client.post(WRITE_URL, data)
    assert_response_code(response, 201)
    assert_no_model("a/1")
    assert_modified_fields(redis_connection, {"a/1": ["f"]})
    reset_redis_data()

    data["events"] = [{"type": "restore", "fqid": "a/1"}]
    response = json_client.post(WRITE_URL, data)
    assert_response_code(response, 201)
    assert_model("a/1", {"f": 1}, 2)
    assert_modified_fields(redis_connection, {"a/1": ["f"]})


def test_restore_without_delete(json_client, data, redis_connection, reset_redis_data):
    response = json_client.post(WRITE_URL, data)
    assert_response_code(response, 201)
    assert_model("a/1", {"f": 1}, 1)
    assert_modified_fields(redis_connection, {"a/1": ["f"]})
    reset_redis_data()

    data["events"] = [{"type": "restore", "fqid": "a/1"}]
    response = json_client.post(WRITE_URL, data)
    assert_error_response(response, ERROR_CODES.MODEL_NOT_DELETED)
    assert_model("a/1", {"f": 1}, 1)
    assert_no_modified_fields(redis_connection)


def test_write_none(json_client, data, redis_connection, reset_redis_data):
    create_model(json_client, data, redis_connection, reset_redis_data)

    data["events"][0] = {"type": "update", "fqid": "a/1", "fields": {"f": None}}
    response = json_client.post(WRITE_URL, data)
    assert_response_code(response, 201)
    assert_model("a/1", {}, 2)
    assert_modified_fields(redis_connection, {"a/1": ["f"]}, meta_deleted=False)


def test_create_delete_restore_different_positions(
    json_client, data, redis_connection, reset_redis_data
):
    create_model(json_client, data, redis_connection, reset_redis_data)

    data["events"][0] = {"type": "delete", "fqid": "a/1"}
    response = json_client.post(WRITE_URL, data)
    assert_response_code(response, 201)
    assert_no_model("a/1")
    assert_modified_fields(redis_connection, {"a/1": ["f"]})
    reset_redis_data()

    data["events"][0] = {"type": "restore", "fqid": "a/1"}

    response = json_client.post(WRITE_URL, data)
    assert_response_code(response, 201)
    assert_model("a/1", {"f": 1}, 3)
    assert_modified_fields(redis_connection, {"a/1": ["f"]})


def test_delete_restore_delete_restore(
    json_client, data, redis_connection, reset_redis_data
):
    create_model(json_client, data, redis_connection, reset_redis_data)

    data["events"][0] = {"type": "delete", "fqid": "a/1"}
    data["events"].append({"type": "restore", "fqid": "a/1"})
    data["events"].append({"type": "delete", "fqid": "a/1"})
    data["events"].append({"type": "restore", "fqid": "a/1"})
    response = json_client.post(WRITE_URL, data)
    assert_response_code(response, 201)
    assert_model("a/1", {"f": 1}, 2)
    assert_modified_fields(redis_connection, {"a/1": ["f"]})


def test_update_delete_restore_update(
    json_client, data, redis_connection, reset_redis_data
):
    create_model(json_client, data, redis_connection, reset_redis_data)

    data["events"][0] = {
        "type": "update",
        "fqid": "a/1",
        "fields": {"another": "value", "f": None},
    }
    data["events"].append({"type": "delete", "fqid": "a/1"})
    data["events"].append({"type": "restore", "fqid": "a/1"})
    data["events"].append(
        {"type": "update", "fqid": "a/1", "fields": {"third_field": ["my", "list"]}}
    )
    response = json_client.post(WRITE_URL, data)
    assert_response_code(response, 201)
    assert_model("a/1", {"another": "value", "third_field": ["my", "list"]}, 2)
    assert_modified_fields(redis_connection, {"a/1": ["f", "another", "third_field"]})


def test_delete_update(json_client, data, redis_connection, reset_redis_data):
    create_model(json_client, data, redis_connection, reset_redis_data)

    data["events"][0] = {"type": "delete", "fqid": "a/1"}
    data["events"].append(
        {
            "type": "update",
            "fqid": "a/1",
            "fields": {"f": 42},
        }
    )
    response = json_client.post(WRITE_URL, data)
    assert_error_response(response, ERROR_CODES.MODEL_DOES_NOT_EXIST)


def test_read_db_is_updated_before_redis_fires(json_client, data):
    messaging = injector.get(Messaging)
    connection_handler = injector.get(ConnectionHandler)

    def assert_read_db_data(*args, **kwargs):
        connection = psycopg2.connect(**connection_handler.get_connection_params())
        with connection.cursor() as cursor:
            cursor.execute("select * from models where fqid = 'a/1'")
            result = cursor.fetchone()

            # assert the model exists
            assert result

    with patch.object(messaging, "handle_events", new=assert_read_db_data):
        response = json_client.post(WRITE_URL, data)
        assert_response_code(response, 201)


def test_two_write_requests(json_client, data, redis_connection, reset_redis_data):
    create_model(json_client, data, redis_connection, reset_redis_data)

    data["events"][0] = {"type": "update", "fqid": "a/1", "fields": {"f": None}}
    data2 = copy.deepcopy(data)
    data2["events"][0] = {"type": "update", "fqid": "a/1", "fields": {"f2": 1}}
    response = json_client.post(WRITE_URL, [data, data2])
    assert_response_code(response, 201)
    assert_model("a/1", {"f2": 1}, 3)
    assert_modified_fields(redis_connection, {"a/1": ["f", "f2"]}, meta_deleted=False)


def test_two_write_requests_with_locked_fields(
    json_client, data, redis_connection, reset_redis_data
):
    create_model(json_client, data, redis_connection, reset_redis_data)

    data["events"][0] = {"type": "update", "fqid": "a/1", "fields": {"f": None}}
    data2 = copy.deepcopy(data)
    data2["events"][0] = {"type": "update", "fqid": "a/1", "fields": {"f2": 1}}
    data2["locked_fields"] = {"a/1/f": 1}
    response = json_client.post(WRITE_URL, [data, data2])
    assert_model("a/1", {"f": 1}, 1)
    assert_error_response(response, ERROR_CODES.MODEL_LOCKED)
    assert_no_modified_fields(redis_connection)
