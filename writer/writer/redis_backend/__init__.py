from .redis_messaging_backend_service import RedisMessagingBackendService  # noqa


def setup_di():
    from shared.di import injector

    from .connection_handler import ConnectionHandler
    from .redis_connection_handler import RedisConnectionHandlerService

    injector.register(ConnectionHandler, RedisConnectionHandlerService)
