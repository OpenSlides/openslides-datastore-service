import os
from typing import Any

import psycopg2
import pytest
import redis

from shared.core import ReadDatabase
from shared.di import injector
from shared.postgresql_backend.pg_connection_handler import (
    ENVIRONMENT_VARIABLES as POSTGRESQL_ENVIRONMENT_VARIABLES,
)
from shared.postgresql_backend.sql_read_database_backend_service import (
    SqlReadDatabaseBackendService,
)
from shared.util import reset_di  # noqa
from shared.util import setup_di as shared_setup_di
from writer.core import Database, Messaging, OccLocker, setup_di as core_setup_di
from writer.flask_frontend import FlaskFrontend
from writer.postgresql_backend import (
    SqlDatabaseBackendService,
    SqlOccLockerBackendService,
    setup_di as postgresql_setup_di,
)
from writer.redis_backend import (
    RedisMessagingBackendService,
    setup_di as redis_setup_di,
)
from writer.redis_backend.redis_connection_handler import (
    ENVIRONMENT_VARIABLES as REDIS_ENVIRONMENT_VARIABLES,
)
from writer.redis_backend.redis_messaging_backend_service import MODIFIED_FIELDS_TOPIC

from .shared import ALL_TABLES


def get_env(name):
    return os.environ.get(name)


# Postgresql

_db_connection = None


@pytest.fixture(scope="session", autouse=True)
def setup_db_connection():
    global _db_connection
    _db_connection = psycopg2.connect(
        host=get_env(POSTGRESQL_ENVIRONMENT_VARIABLES.HOST),
        port=int(get_env(POSTGRESQL_ENVIRONMENT_VARIABLES.PORT) or 5432),
        database=get_env(POSTGRESQL_ENVIRONMENT_VARIABLES.NAME),
        user=get_env(POSTGRESQL_ENVIRONMENT_VARIABLES.USER),
        password=get_env(POSTGRESQL_ENVIRONMENT_VARIABLES.PASSWORD),
    )
    _db_connection.autocommit = False
    yield _db_connection
    _db_connection.close()


@pytest.fixture()
def db_connection():
    global _db_connection
    yield _db_connection


@pytest.fixture(autouse=True)
def reset_db_data(db_connection):
    with db_connection:
        with db_connection.cursor() as cur:
            for table in ALL_TABLES:
                cur.execute(f"DELETE FROM {table}")

            # Reset all sequences.
            cur.execute("select c.relname from pg_class c where c.relkind='S'")
            for (relname,) in cur.fetchall():
                cur.execute(f"alter sequence {relname} restart with 1")
    yield


@pytest.fixture()
def db_cur(db_connection):
    with db_connection:
        with db_connection.cursor() as cur:
            yield cur


@pytest.fixture(scope="session", autouse=True)
def reset_db_schema(setup_db_connection):
    conn = setup_db_connection
    with conn:
        with conn.cursor() as cur:
            drop_db_definitions(cur)
            schema = get_db_schema_definition()
            cur.execute(schema)


def drop_db_definitions(cur):
    for table in ALL_TABLES:
        cur.execute(f"DROP TABLE IF EXISTS {table} CASCADE")
    cur.execute("DROP TYPE IF EXISTS event_type CASCADE")


def get_db_schema_definition():
    with open("./shared/postgresql_backend/schema.sql") as f:
        return f.read()


# Redis

_redis_connection: Any = None


def xadd_callback_noop(response, **options):
    return response


@pytest.fixture(scope="session", autouse=True)
def setup_redis_connection():
    global _redis_connection
    _redis_connection = redis.Redis(
        host=get_env(REDIS_ENVIRONMENT_VARIABLES.HOST),
        port=int(get_env(REDIS_ENVIRONMENT_VARIABLES.PORT) or 6379),
    )
    _redis_connection.set_response_callback("XREAD", xadd_callback_noop)
    yield _redis_connection
    _redis_connection.close()


@pytest.fixture()
def redis_connection():
    global _redis_connection
    yield _redis_connection


@pytest.fixture(autouse=True)
def reset_redis_data(redis_connection):
    def reset_fn():
        redis_connection.xtrim(MODIFIED_FIELDS_TOPIC, 0, approximate=False)

    reset_fn()
    yield reset_fn


# Application


@pytest.fixture(autouse=True)
def setup_di(reset_di):  # noqa
    shared_setup_di()
    postgresql_setup_di()
    redis_setup_di()
    injector.register(ReadDatabase, SqlReadDatabaseBackendService)
    injector.register(Database, SqlDatabaseBackendService)
    injector.register(OccLocker, SqlOccLockerBackendService)
    injector.register(Messaging, RedisMessagingBackendService)
    core_setup_di()


@pytest.fixture
def app(setup_di):
    application = FlaskFrontend.create_application()
    yield application


# Flask


@pytest.fixture()
def json_client(client):
    old_post = client.post

    def post(url, data):
        response = old_post(url, json=data)

        # assert response.is_json
        return response

    client.post = post
    yield client
    client.post = old_post
