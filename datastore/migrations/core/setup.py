from typing import Type

from datastore.migrations.core.migration_reader import MigrationReader
from datastore.reader import setup_di as reader_setup_di
from datastore.shared.di import injector
from datastore.shared.postgresql_backend import setup_di as shared_postgresql_setup_di
from datastore.shared.services import setup_di as util_setup_di
from datastore.writer import setup_di as writer_setup_di
from datastore.writer.postgresql_backend import setup_di as writer_postgresql_setup_di
from datastore.writer.redis_backend import setup_di as redis_setup_di

from .migration_handler import MigrationHandler
from .migration_logger import MigrationLogger, PrintFunction


def register_services(memory_only: bool = False):
    from .migraters import EventMigrater, ModelMigrater
    from .migration_logger import MigrationLogger, MigrationLoggerImplementation

    EventMigraterImplementation: Type[EventMigrater]
    ModelMigraterImplementation: Type[ModelMigrater]
    MigrationHandlerImplementation: Type[MigrationHandler]
    MigrationReaderImplementation: Type[MigrationReader]
    if memory_only:
        from .migraters.event_migrater_memory import (
            EventMigraterImplementationMemory as EventMigraterImplementation,
        )
        from .migraters.model_migrater_memory import (
            ModelMigraterImplementationMemory as ModelMigraterImplementation,
        )
        from .migration_handler import (
            MigrationHandlerImplementationMemory as MigrationHandlerImplementation,
        )
        from .migration_reader import (
            MigrationReaderImplementationMemory as MigrationReaderImplementation,
        )

        writer_postgresql_setup_di()
    else:
        from .migraters.event_migrater import EventMigraterImplementation
        from .migraters.model_migrater import ModelMigraterImplementation
        from .migration_handler import MigrationHandlerImplementation
        from .migration_reader import MigrationReaderImplementation

        util_setup_di()
        shared_postgresql_setup_di()
        redis_setup_di()
        writer_setup_di()
        reader_setup_di()

    injector.register(MigrationLogger, MigrationLoggerImplementation)
    injector.register(MigrationHandler, MigrationHandlerImplementation)
    injector.register(EventMigrater, EventMigraterImplementation)
    injector.register(ModelMigrater, ModelMigraterImplementation)
    injector.register(MigrationReader, MigrationReaderImplementation)


def setup(
    verbose: bool = False, print_fn: PrintFunction = print, memory_only: bool = False
) -> MigrationHandler:
    register_services(memory_only)
    logger = injector.get(MigrationLogger)
    logger.set_verbose(verbose)
    logger.set_print_fn(print_fn)
    return injector.get(MigrationHandler)
