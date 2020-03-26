from typing import Any

import pytest
import redis

from shared.di import injector
from shared.postgresql_backend import setup_di as postgresql_setup_di
from shared.tests import (  # noqa
    db_connection,
    db_cur,
    get_env,
    json_client,
    reset_db_data,
    reset_db_schema,
    reset_di,
    setup_db_connection,
)
from shared.util import setup_di as util_setup_di
from writer.core import Database, Messaging, OccLocker, setup_di as core_setup_di
from writer.flask_frontend import FlaskFrontend
from writer.postgresql_backend import (
    SqlDatabaseBackendService,
    SqlOccLockerBackendService,
)
from writer.redis_backend import (
    RedisMessagingBackendService,
    setup_di as redis_setup_di,
)
from writer.redis_backend.redis_connection_handler import (
    ENVIRONMENT_VARIABLES as REDIS_ENVIRONMENT_VARIABLES,
)
from writer.redis_backend.redis_messaging_backend_service import MODIFIED_FIELDS_TOPIC


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
    util_setup_di()
    postgresql_setup_di()
    redis_setup_di()
    injector.register(Database, SqlDatabaseBackendService)
    injector.register(OccLocker, SqlOccLockerBackendService)
    injector.register(Messaging, RedisMessagingBackendService)
    core_setup_di()


@pytest.fixture
def app(setup_di):
    application = FlaskFrontend.create_application()
    yield application
