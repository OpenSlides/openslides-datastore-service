import copy
from unittest.mock import patch

import psycopg2
import pytest

from datastore.shared.di import injector
from datastore.shared.flask_frontend import ERROR_CODES
from datastore.shared.postgresql_backend import ConnectionHandler
from datastore.shared.postgresql_backend.sql_read_database_backend_service import (
    MIGRATION_INDEX_NOT_INITIALIZED,
)
from datastore.shared.services import ReadDatabase
from datastore.writer.core import Messaging
from datastore.writer.flask_frontend.routes import WRITE_URL
from tests.util import assert_error_response, assert_response_code
from tests.writer.system.util import (
    assert_model,
    assert_modified_fields,
    assert_no_modified_fields,
)


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


def test_migration_index(
    json_client, data, db_connection, db_cur, redis_connection, reset_redis_data
):
    create_model(json_client, data, redis_connection, reset_redis_data)

    # change the migration index and reset the read DB
    db_cur.execute("update positions set migration_index=3 where position=1", [])
    db_connection.commit()
    injector.get(ReadDatabase).current_migration_index = MIGRATION_INDEX_NOT_INITIALIZED

    data["events"][0] = {"type": "update", "fqid": "a/1", "fields": {"f": 2}}
    response = json_client.post(WRITE_URL, [data])
    assert_response_code(response, 201)
    assert_model("a/1", {"f": 2}, 2)

    db_cur.execute("select migration_index from positions where position=%s", [2])
    migration_index = db_cur.fetchone()[0]
    assert migration_index == 3


def test_varying_migration_indices(
    json_client, data, db_connection, db_cur, redis_connection, reset_redis_data
):
    # create two positions
    create_model(json_client, data, redis_connection, reset_redis_data)

    data["events"][0] = {"type": "update", "fqid": "a/1", "fields": {"f": 2}}
    response = json_client.post(WRITE_URL, [data])
    assert_response_code(response, 201)
    assert_model("a/1", {"f": 2}, 2)

    # modify the migration index of the second position and reset the read db
    db_cur.execute("update positions set migration_index=3 where position=2", [])
    db_connection.commit()
    injector.get(ReadDatabase).current_migration_index = MIGRATION_INDEX_NOT_INITIALIZED

    data["events"][0] = {"type": "update", "fqid": "a/1", "fields": {"f": 3}}
    response = json_client.post(WRITE_URL, [data])
    assert_error_response(response, ERROR_CODES.INVALID_DATASTORE_STATE)
    assert_model("a/1", {"f": 2}, 2)
