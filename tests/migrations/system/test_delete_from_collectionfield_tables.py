from datastore.shared.flask_frontend import ERROR_CODES
from datastore.writer.flask_frontend.routes import WRITE_URL
from tests.util import assert_error_response, assert_response_code


def test_delete_from_tables(migration_handler, write, query_single_value, assert_count):
    write({"type": "create", "fqid": "a/1", "fields": {"f": 1}})
    write({"type": "update", "fqid": "a/1", "fields": {"f": 2}})

    assert query_single_value("select count(*) from collectionfields", []) > 0
    assert query_single_value("select count(*) from events_to_collectionfields", []) > 0

    migration_handler.delete_collectionfield_aux_tables()

    assert_count("collectionfields", 0)
    assert_count("events_to_collectionfields", 0)


def test_locking_works_afterwards_ok(
    migration_handler, write, writer, query_single_value
):
    write({"type": "create", "fqid": "a/1", "fields": {"f": 1}})  # position 1
    migration_handler.delete_collectionfield_aux_tables()
    write({"type": "update", "fqid": "a/1", "fields": {"f": 2}})  # position 2

    payload = {
        "user_id": 1,
        "information": {},
        "locked_fields": {"a/f": 2},
        "events": [{"type": "update", "fqid": "a/1", "fields": {"f": 3}}],
    }
    response = writer.post(WRITE_URL, payload)
    assert_response_code(response, 201)


def test_locking_works_afterwards_lock(
    migration_handler, write, writer, query_single_value
):
    write({"type": "create", "fqid": "a/1", "fields": {"f": 1}})  # position 1
    migration_handler.delete_collectionfield_aux_tables()
    write({"type": "update", "fqid": "a/1", "fields": {"f": 2}})  # position 2

    payload = {
        "user_id": 1,
        "information": {},
        "locked_fields": {"a/f": 1},  # !
        "events": [{"type": "update", "fqid": "a/1", "fields": {"f": 3}}],
    }
    response = writer.post(WRITE_URL, payload)
    assert_error_response(response, ERROR_CODES.MODEL_LOCKED)
