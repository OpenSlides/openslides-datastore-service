from typing import Set

from shared.core import ReadDatabase
from shared.di import injector
from shared.postgresql_backend import EVENT_TYPES, ConnectionHandler
from shared.util import META_DELETED, META_POSITION
from writer.redis_backend.redis_messaging_backend_service import MODIFIED_FIELDS_TOPIC


ALL_TABLES = (
    "positions",
    "events",
    "models_lookup",
    "id_sequences",
    "collectionfields",
    "events_to_collectionfields",
    "models",
)

WRITE_URL = "/internal/datastore/writer/write"
GET_IDS_URL = "/internal/datastore/writer/get_ids"


def assert_error_response(response, type):
    assert response.status_code == 400
    assert isinstance(response.json.get("error"), dict)
    assert response.json["error"].get("type") == type


def assert_model(fqid, model, position):
    connection_handler = injector.get(ConnectionHandler)
    with connection_handler.get_connection_context():
        # read from read db
        read_db = injector.get(ReadDatabase)
        read_db_models = read_db.get_models([fqid])
        # if meta_deleted:
        model[META_DELETED] = False
        model[META_POSITION] = position
        read_db_model = read_db_models.get(fqid)
        assert read_db_model == model

        # build model and assert that the last event is not a deleted.
        builded_model = read_db.build_model_ignore_deleted(fqid)
        del model[META_POSITION]
        assert builded_model == model
        event_type = connection_handler.query_single_value(
            "select type from events where fqid=%s order by id desc limit 1", [fqid]
        )
        assert (
            isinstance(event_type, str)
            and len(event_type) > 0
            and event_type != EVENT_TYPES.DELETE
        )


def assert_no_model(fqid):
    connection_handler = injector.get(ConnectionHandler)
    with connection_handler.get_connection_context():
        # read from read db
        read_db = injector.get(ReadDatabase)
        read_db_models = read_db.get_models([fqid])
        assert fqid not in read_db_models

        # assert last event is a deleted one
        event_type = connection_handler.query_single_value(
            "select type from events where fqid=%s order by id desc limit 1", [fqid]
        )
        assert event_type in (EVENT_TYPES.DELETE, None)


def assert_no_db_entry(db_cur):
    for table in ALL_TABLES:
        db_cur.execute(f"select count(*) from {table}")
        assert db_cur.fetchone()[0] == 0


def assert_modified_fields(redis_connection, fields_per_fqid, meta_deleted=True):
    modified_fields: Set[str] = set()
    for fqid, fields in fields_per_fqid.items():
        modified_fields.update(fqid + "/" + field for field in fields)
        if meta_deleted:
            modified_fields.add(fqid + "/" + META_DELETED)
        modified_fields.add(fqid + "/" + META_POSITION)

    assert redis_connection.xlen(MODIFIED_FIELDS_TOPIC) == 1
    response = redis_connection.xread({MODIFIED_FIELDS_TOPIC: 0}, count=1)
    data = response[0][1][0][1]  # wtf?
    redis_modified_fields = set(
        field.decode("utf-8") for field in data[1::2]
    )  # skip every second "modified" entry
    assert modified_fields == redis_modified_fields


def assert_no_modified_fields(redis_connection):
    assert redis_connection.xlen(MODIFIED_FIELDS_TOPIC) == 0
