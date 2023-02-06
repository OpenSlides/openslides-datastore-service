from typing import Any, Dict, Optional

import redis

from datastore.shared.di import service_as_singleton
from datastore.shared.services import EnvironmentService, ShutdownService


# TODO: Test this. Add something like a @ensure_connection decorator, that wraps a
# function that uses redis. It should ensure, that there is a connection (create one
# if not) and should retry the operation, if there was some kind of connection error.
# Note: Which one is a connection error?


class ENVIRONMENT_VARIABLES:
    HOST = "MESSAGE_BUS_HOST"
    PORT = "MESSAGE_BUS_PORT"


@service_as_singleton
class RedisConnectionHandlerService:
    environment: EnvironmentService
    shutdown_service: ShutdownService
    connection: Optional[Any] = None

    def __init__(self, shutdown_service: ShutdownService):
        shutdown_service.register(self)

    def ensure_connection(self):
        if not self.connection:
            self.connection = self.get_connection()
        else:
            # todo check if alive
            pass
        return self.connection

    def get_connection(self):
        host = self.environment.get(ENVIRONMENT_VARIABLES.HOST)
        port = int(self.environment.try_get(ENVIRONMENT_VARIABLES.PORT) or 6379)
        return redis.Redis(host=host, port=port)

    def xadd(self, topic: str, fields: Dict[str, str]) -> None:
        if not fields or not topic:
            return
        connection = self.ensure_connection()
        connection.xadd(topic, fields)

    def shutdown(self):
        if self.connection:
            self.connection.close()
            self.connection = None
