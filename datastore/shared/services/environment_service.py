import os
from typing import Dict, Optional, cast

from datastore.shared.di import service_as_singleton


DATASTORE_DEV_MODE_ENVIRONMENT_VAR = "DATASTORE_ENABLE_DEV_ENVIRONMENT"


class EnvironmentVariableMissing(Exception):
    def __init__(self, name: str):
        self.name = name


@service_as_singleton
class EnvironmentService:
    def __init__(self):
        self.cache: Dict[str, Optional[str]] = {}

    def try_get(self, name: str) -> Optional[str]:
        self.ensure_cache(name)
        return self.cache.get(name)

    def get(self, name: str) -> str:
        self.ensure_cache(name)
        if not self.cache.get(name):
            raise EnvironmentVariableMissing(name)
        return cast(str, self.cache[name])

    def set(self, name: str, value: str) -> None:
        self.cache[name] = value

    def ensure_cache(self, name: str) -> None:
        if name not in self.cache:
            self.cache[name] = os.environ.get(name, None)

    def is_dev_mode(self) -> bool:
        value = self.try_get(DATASTORE_DEV_MODE_ENVIRONMENT_VAR)
        return value is not None and value.lower() in ("1", "on", "yes", "true")
