from datastore.reader import setup_di as reader_setup_di
from datastore.shared.di import injector
from datastore.shared.postgresql_backend import setup_di as postgresql_setup_di
from datastore.shared.services import setup_di as util_setup_di
from datastore.writer import setup_di as writer_setup_di
from datastore.writer.redis_backend import setup_di as redis_setup_di

from .migration_handler import MigrationHandler
from .migration_logger import MigrationLogger, PrintFunction


def register_services():
    util_setup_di()
    postgresql_setup_di()
    redis_setup_di()
    writer_setup_di()
    reader_setup_di()

    from .migrater import Migrater, MigraterImplementation
    from .migration_handler import MigrationHandlerImplementation
    from .migration_logger import MigrationLogger, MigrationLoggerImplementation

    injector.register(MigrationLogger, MigrationLoggerImplementation)
    injector.register(Migrater, MigraterImplementation)
    injector.register(MigrationHandler, MigrationHandlerImplementation)


def setup(verbose: bool = False, print_fn: PrintFunction = print) -> MigrationHandler:
    register_services()
    logger = injector.get(MigrationLogger)
    logger.set_verbose(verbose)
    logger.set_print_fn(print_fn)
    return injector.get(MigrationHandler)
