import atexit

from reader.core import setup_di as core_setup_di
from reader.flask_frontend import FlaskFrontend
from shared.di import injector
from shared.postgresql_backend import setup_di as postgresql_setup_di
from shared.services import ShutdownService, setup_di as util_setup_di


def register_services():
    util_setup_di()
    postgresql_setup_di()
    core_setup_di()


def create_application():
    register_services()

    def shutdown():
        shutdown_service = injector.get(ShutdownService)
        shutdown_service.shutdown()

    atexit.register(shutdown)

    # TODO: set flask logging to the gunicorn logger, if available
    application = FlaskFrontend.create_application()
    return application


application = create_application()
