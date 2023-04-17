from .redis_messaging_backend_service import RedisMessagingBackendService


def setup_di():
    from datastore.shared.di import injector

    from .connection_handler import ConnectionHandler
    from .redis_connection_handler import RedisConnectionHandlerService

    injector.register(ConnectionHandler, RedisConnectionHandlerService)
