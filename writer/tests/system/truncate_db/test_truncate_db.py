import pytest

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


GLOB = {}


@pytest.mark.skip(reason="Only for performance testing")
def test_truncate_db_perf(db_connection, db_cur, json_client):
    from time import time
    from unittest.mock import patch

    GLOB["orig_post"] = json_client.post
    GLOB["tot"] = 0
    count = 100

    def post(*args, **kwargs):
        start = time()
        result = GLOB["orig_post"](*args, **kwargs)
        GLOB["tot"] += time() - start
        return result

    with patch.object(json_client, "post", post):
        for i in range(count):
            test_truncate_db(db_connection, db_cur, json_client)
    tot = GLOB["tot"]
    print(f"Total: {tot}")
    print(f"per call: {tot / count}")


def test_not_found_in_non_dev(json_client):
    injector.get(EnvironmentService).set(DATASTORE_DEV_MODE_ENVIRONMENT_VAR, "0")
    response = json_client.post(TRUNCATE_DB_URL, {})
    assert_response_code(response, 404)
