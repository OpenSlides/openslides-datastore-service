import copy

import pytest

from datastore.shared.di import injector
from datastore.shared.flask_frontend import ERROR_CODES
from datastore.shared.postgresql_backend import ConnectionHandler
from datastore.shared.services import ReadDatabase
from datastore.shared.util import DeletedModelsBehaviour, MappedFields
from datastore.writer.flask_frontend.routes import WRITE_URL
from tests.util import assert_error_response, assert_response_code
from tests.writer.system.util import (
    assert_modified_fields,
    assert_no_model,
    assert_no_modified_fields,
)

from .test_write import create_model


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
        model = read_db.get(
            "a/1",
            MappedFields(),
            get_deleted_models=DeletedModelsBehaviour.ONLY_DELETED,
        )
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
