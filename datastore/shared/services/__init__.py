from .environment_service import EnvironmentService, EnvironmentVariableMissing  # noqa
from .read_database import ReadDatabase  # noqa
from .shutdown_service import ShutdownService


def setup_di():
    from datastore.shared.di import injector

    injector.register(EnvironmentService, EnvironmentService)
    injector.register(ShutdownService, ShutdownService)
