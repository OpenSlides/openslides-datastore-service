from datastore.reader import setup_di as reader_setup_di
from datastore.shared.di import injector
from datastore.shared.postgresql_backend import setup_di as postgresql_setup_di
from datastore.shared.services import setup_di as util_setup_di
from datastore.writer import setup_di as writer_setup_di
from datastore.writer.redis_backend import setup_di as redis_setup_di

from .migration_handler import MigrationHandler
from .migration_logger import MigrationLogger, PrintFunction


def register_services(memory_only: bool = False):
    if not memory_only:
        util_setup_di()
        postgresql_setup_di()
        redis_setup_di()
        writer_setup_di()
        reader_setup_di()

    from .migrater import Migrater, MigraterImplementation
    from .migration_handler import (
        MigrationHandlerImplementation,
        MigrationHandlerImplementationMemory,
    )
    from .migration_logger import MigrationLogger, MigrationLoggerImplementation

    injector.register(MigrationLogger, MigrationLoggerImplementation)
    if memory_only:
        from .migrater_memory import MigraterImplementationMemory

        injector.register(MigrationHandler, MigrationHandlerImplementationMemory)
        injector.register(Migrater, MigraterImplementationMemory)
    else:
        injector.register(MigrationHandler, MigrationHandlerImplementation)
        injector.register(Migrater, MigraterImplementation)


def setup(
    verbose: bool = False, print_fn: PrintFunction = print, memory_only: bool = False
) -> MigrationHandler:
    register_services(memory_only)
    logger = injector.get(MigrationLogger)
    logger.set_verbose(verbose)
    logger.set_print_fn(print_fn)
    return injector.get(MigrationHandler)
