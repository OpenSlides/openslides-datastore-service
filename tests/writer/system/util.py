from typing import Dict, List, Set

import pytest

from datastore.shared.di import injector
from datastore.shared.postgresql_backend import ALL_TABLES, ConnectionHandler
from datastore.shared.postgresql_backend.sql_event_types import EVENT_TYPE
from datastore.shared.services import ReadDatabase
from datastore.shared.typing import Field, Fqid
from datastore.shared.util import (
    META_DELETED,
    META_POSITION,
    ModelDoesNotExist,
    fqfield_from_fqid_and_field,
)
from datastore.writer.redis_backend.redis_messaging_backend_service import (
    MODIFIED_FIELDS_TOPIC,
)


def assert_model(fqid, model, position):
    connection_handler = injector.get(ConnectionHandler)
    with connection_handler.get_connection_context():
        # read from read db
        read_db = injector.get(ReadDatabase)
        read_db_model = read_db.get(fqid)

        model[META_DELETED] = False
        model[META_POSITION] = position
        assert read_db_model == model

        # build model and assert that the last event is not a deleted.
        built_model = read_db.build_model_ignore_deleted(fqid)
        assert built_model == model
        event_type = connection_handler.query_single_value(
            "select type from events where fqid=%s order by position desc, weight desc limit 1",
            [fqid],
        )
        assert (
            isinstance(event_type, str)
            and len(event_type) > 0
            and event_type != EVENT_TYPE.DELETE
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
            "select type from events where fqid=%s order by position desc, weight desc limit 1",
            [fqid],
        )
        assert event_type in (EVENT_TYPE.DELETE, None)


def assert_no_db_entry(db_cur):
    for table in ALL_TABLES:
        db_cur.execute(f"select count(*) from {table}")
        assert db_cur.fetchone()[0] == 0


def assert_modified_fields(
    redis_connection, fields_per_fqid: Dict[Fqid, List[Field]], meta_deleted=True
):
    modified_fields: Set[str] = set()
    for fqid, fields in fields_per_fqid.items():
        modified_fields.update(
            fqfield_from_fqid_and_field(fqid, field) for field in fields
        )
        if meta_deleted:
            modified_fields.add(fqfield_from_fqid_and_field(fqid, META_DELETED))
        modified_fields.add(fqfield_from_fqid_and_field(fqid, META_POSITION))

    assert modified_fields == get_redis_modified_fields(redis_connection)


def get_redis_modified_fields(redis_connection):
    assert redis_connection.xlen(MODIFIED_FIELDS_TOPIC) == 1
    response = redis_connection.xread({MODIFIED_FIELDS_TOPIC: 0}, count=1)
    data = response[0][1][0][1]  # wtf?
    return set(fqfield.decode("utf-8") for fqfield in data[::2])


def assert_no_modified_fields(redis_connection):
    assert redis_connection.xlen(MODIFIED_FIELDS_TOPIC) == 0
