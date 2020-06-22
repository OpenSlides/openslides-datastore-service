import os

from shared.di import injector
from shared.services import EnvironmentService
from shared.services.environment_service import DATASTORE_DEV_MODE_ENVIRONMENT_VAR
from shared.tests.util import assert_response_code
from shared.util import ALL_TABLES
from writer.flask_frontend.routes import TRUNCATE_DB_URL


def test_truncate_db(db_connection, db_cur, json_client):
    db_cur.execute("insert into positions (user_id) values ('1')")
    db_cur.execute(
        "insert into events (position, fqid, type) values (1, 'a/1', 'create')"
    )
    db_cur.execute("insert into models_lookup values ('a/1', TRUE)")
    db_cur.execute("insert into id_sequences values ('c', 1)")
    db_cur.execute(
        "insert into collectionfields (collectionfield, position) values ('c/f', 1)"
    )
    db_cur.execute("insert into events_to_collectionfields values (1, 1)")
    db_cur.execute("insert into models values ('c/1', '{}')")
    db_connection.commit()

    response = json_client.post(TRUNCATE_DB_URL, {})
    assert_response_code(response, 204)

    with db_connection.cursor() as cursor:
        for table in ALL_TABLES:
            cursor.execute(f"select * from {table}")
            assert cursor.fetchone() is None


def test_not_found(json_client):
    del os.environ[DATASTORE_DEV_MODE_ENVIRONMENT_VAR]
    injector.get(EnvironmentService).cache = {}
    response = json_client.post(TRUNCATE_DB_URL, {})
    assert_response_code(response, 404)
