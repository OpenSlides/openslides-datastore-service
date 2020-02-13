import atexit

from writer.core import (
    Database,
    Messaging,
    OccLocker,
    ReadDatabase,
    setup_di as core_setup_di,
)
from writer.di import injector
from writer.flask_frontend import FlaskFrontend
from writer.postgresql_backend import (
    SqlDatabaseBackendService,
    SqlOccLockerBackendService,
    SqlReadDatabaseBackendService,
    setup_di as postgresql_setup_di,
)
from writer.redis_backend import (
    RedisMessagingBackendService,
    setup_di as redis_setup_di,
)
from writer.shared import ShutdownService, setup_di as shared_setup_di


def register_services():
    shared_setup_di()
    postgresql_setup_di()
    redis_setup_di()
    injector.register(Database, SqlDatabaseBackendService)
    injector.register(ReadDatabase, SqlReadDatabaseBackendService)
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
