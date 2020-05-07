from typing import Set

import pytest

from shared.di import injector
from shared.postgresql_backend import ConnectionHandler
from shared.postgresql_backend.sql_event_types import EVENT_TYPES
from shared.services import ReadDatabase
from shared.tests.util import ALL_TABLES
from shared.util import META_DELETED, META_POSITION, ModelDoesNotExist
from writer.redis_backend.redis_messaging_backend_service import MODIFIED_FIELDS_TOPIC


WRITE_URL = "/internal/datastore/writer/write"
RESERVE_IDS_URL = "/internal/datastore/writer/reserve_ids"


def assert_model(fqid, model, position):
    connection_handler = injector.get(ConnectionHandler)
    with connection_handler.get_connection_context():
        # read from read db
        read_db = injector.get(ReadDatabase)
        read_db_model = read_db.get(fqid)

        model[META_DELETED] = False
        model[META_POSITION] = position
        if read_db_model != model:
            print(read_db_model)
        assert read_db_model == model

        # build model and assert that the last event is not a deleted.
        built_model = read_db.build_model_ignore_deleted(fqid)
        del model[META_POSITION]
        del built_model[META_POSITION]
        assert built_model == model
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

        with pytest.raises(ModelDoesNotExist):
            read_db.get(fqid)

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
