from typing import Any

from .environment_service import EnvironmentService, EnvironmentVariableMissing  # noqa
from .reset_di import reset_di  # noqa
from .shutdown_service import ShutdownService


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
