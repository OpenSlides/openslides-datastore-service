import atexit
import os

from shared.di import injector
from shared.services import ShutdownService
from shared.util.logging import init_logging


def create_base_application(flask_frontend):
    # overwrite the builtin print to always flush
    def flushprint(*args, **kwargs):
        if "flush" not in kwargs:
            kwargs["flush"] = True

        __builtins__["oldprint"](*args, **kwargs)  # type: ignore

    if "oldprint" not in __builtins__:  # type: ignore
        __builtins__["oldprint"] = __builtins__["print"]  # type: ignore
    __builtins__["print"] = flushprint  # type: ignore

    def shutdown():
        shutdown_service = injector.get(ShutdownService)
        shutdown_service.shutdown()

    atexit.register(shutdown)

    application = flask_frontend.create_application()

    # Adapt the gunicorn handlers if gunicorn is used
    is_gunicorn = "gunicorn" in os.environ.get("SERVER_SOFTWARE", "")
    if is_gunicorn:
        init_logging("gunicorn.error", application.logger)
    else:
        init_logging()

    return application
