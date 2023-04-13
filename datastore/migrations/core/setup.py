from datastore.reader import setup_di as reader_setup_di
from datastore.shared.di import injector
from datastore.shared.postgresql_backend import setup_di as postgresql_setup_di
from datastore.shared.services import setup_di as util_setup_di
from datastore.writer import setup_di as writer_setup_di
from datastore.writer.redis_backend import setup_di as redis_setup_di

from .migration_handler import MigrationHandler
from .migration_logger import MigrationLogger, PrintFunction


def register_services(memory_only: bool = False):
    from .migraters.interface import EventMigrater
    from .migration_logger import MigrationLogger, MigrationLoggerImplementation

    if memory_only:
        from .migraters.event_migrater_memory import (
            EventMigraterImplementationMemory as MigraterImplementation,
        )
        from .migration_handler import (
            MigrationHandlerImplementationMemory as MigrationHandlerImplementation,
        )
    else:
        # type-ignoring comments necessary because of https://github.com/python/mypy/issues/13914
        from .migraters.event_migrater import (  # type: ignore[no-redef]
            EventMigraterImplementation as MigraterImplementation,
        )
        from .migration_handler import (  # type: ignore[no-redef]
            MigrationHandlerImplementation,
        )

        util_setup_di()
        postgresql_setup_di()
        redis_setup_di()
        writer_setup_di()
        reader_setup_di()

    injector.register(MigrationLogger, MigrationLoggerImplementation)
    injector.register(MigrationHandler, MigrationHandlerImplementation)
    injector.register(EventMigrater, MigraterImplementation)


def setup(
    verbose: bool = False, print_fn: PrintFunction = print, memory_only: bool = False
) -> MigrationHandler:
    register_services(memory_only)
    logger = injector.get(MigrationLogger)
    logger.set_verbose(verbose)
    logger.set_print_fn(print_fn)
    return injector.get(MigrationHandler)
