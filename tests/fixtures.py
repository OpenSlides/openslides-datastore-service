import os
from typing import Any

import psycopg2
import pytest

from datastore.shared.di import injector
from datastore.shared.postgresql_backend.pg_connection_handler import (
    DATABASE_ENVIRONMENT_VARIABLES as POSTGRESQL_ENVIRONMENT_VARIABLES,
)
from datastore.shared.util import ALL_TABLES


def get_env(name):
    return os.environ.get(name)


def drop_db_definitions(cur):
    for table in ALL_TABLES:
        cur.execute(f"DROP TABLE IF EXISTS {table} CASCADE")
    cur.execute("DROP TYPE IF EXISTS event_type CASCADE")


def get_db_schema_definition():
    with open("datastore/shared/postgresql_backend/schema.sql") as f:
        return f.read()


@pytest.fixture(autouse=True)
def reset_di():
    injector.provider_map = {}


# Postgresql

_db_connection: Any = None


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


# Flask


@pytest.fixture()
def json_client(client):
    old_post = client.post

    def post(url, data):
        response = old_post(
            url, json=data, headers={"content-type": "application/json"}
        )

        # assert response.is_json
        return response

    client.post = post
    yield client
    client.post = old_post
