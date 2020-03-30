import atexit

from shared.di import injector
from shared.postgresql_backend import setup_di as postgresql_setup_di
from shared.postgresql_backend.sql_read_database_backend_service import (
    SqlReadDatabaseBackendService,
)
from shared.services import ReadDatabase, ShutdownService, setup_di as util_setup_di
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

    def shutdown():
        shutdown_service = injector.get(ShutdownService)
        shutdown_service.shutdown()

    atexit.register(shutdown)

    # TODO: set flask logging to the gunicorn logger, if available
    application = FlaskFrontend.create_application()
    return application


application = create_application()
