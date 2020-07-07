import logging
import sys

from shared.di import injector
from shared.services import EnvironmentService
from shared.util import BadCodingError


logger = logging.getLogger("datastore")


def init_logging(reference_logger_name=None, flask_logger=None):
    env_service = injector.get(EnvironmentService)
    level = env_service.try_get("DATASTORE_LOG_LEVEL") or "DEBUG"
    logger.setLevel(level)

    if not logger.handlers:
        formatter = logging.Formatter(
            fmt="%(asctime)s.%(msecs)03d: [%(pathname)s] [%(levelname)s] %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S",
        )
        handler = logging.StreamHandler(sys.stdout)
        handler.flush = sys.stdout.flush  # type: ignore
        handler.setLevel(level)
        handler.setFormatter(formatter)

        logger.addHandler(handler)

    if reference_logger_name:
        if not flask_logger:
            raise BadCodingError(
                "You have to give a flask logger to overwrite with a reference logger!"
            )
        # Overwrite all important handlers to redirect all output where we want it
        for curr_logger in (logger, flask_logger, logging.getLogger("werkzeug")):
            reference_logger = logging.getLogger(reference_logger_name)
            curr_logger.handlers = reference_logger.handlers
