from typing import Any

from .environment_service import EnvironmentService, EnvironmentVariableMissing  # noqa
from .shutdown_service import ShutdownService
from .typing import JSON, Model  # noqa


META_FIELD_PREFIX = "meta"
KEYSEPARATOR = "/"
META_DELETED = f"{META_FIELD_PREFIX}_deleted"
META_POSITION = f"{META_FIELD_PREFIX}_position"


def is_reserved_field(field: Any) -> bool:
    return isinstance(field, str) and field.startswith(META_FIELD_PREFIX)


def setup_di():
    from shared.di import injector

    injector.register(EnvironmentService, EnvironmentService)
    injector.register(ShutdownService, ShutdownService)


class BadCodingError(RuntimeError):
    """
    Should be thrown for errors that theoretically should never happen, except when the
    programmer fucked up.
    """

    pass
