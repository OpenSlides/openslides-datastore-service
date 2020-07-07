from shared import create_base_application
from shared.di import injector
from shared.postgresql_backend import setup_di as postgresql_setup_di
from shared.postgresql_backend.sql_read_database_backend_service import (
    SqlReadDatabaseBackendService,
)
from shared.services import ReadDatabase, setup_di as util_setup_di
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


def register_services():
    util_setup_di()
    postgresql_setup_di()
    redis_setup_di()
    injector.register(ReadDatabase, SqlReadDatabaseBackendService)
    injector.register(Database, SqlDatabaseBackendService)
    injector.register(OccLocker, SqlOccLockerBackendService)
    injector.register(Messaging, RedisMessagingBackendService)
    core_setup_di()


def create_application():
    register_services()
    return create_base_application(FlaskFrontend)


application = create_application()
