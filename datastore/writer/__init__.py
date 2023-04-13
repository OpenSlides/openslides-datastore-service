from . import core, flask_frontend, postgresql_backend, redis_backend


def setup_di():
    from datastore.shared.di import injector

    from .core import Database, Messaging, OccLocker, setup_di as core_setup_di
    from .postgresql_backend import (
        SqlDatabaseBackendService,
        SqlOccLockerBackendService,
        setup_di as postgresql_backend_setup_di,
    )
    from .redis_backend import RedisMessagingBackendService

    core_setup_di()
    postgresql_backend_setup_di()
    injector.register(Database, SqlDatabaseBackendService)
    injector.register(OccLocker, SqlOccLockerBackendService)
    injector.register(Messaging, RedisMessagingBackendService)
