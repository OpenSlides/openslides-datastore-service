import os
from unittest.mock import MagicMock, patch

import pytest

from shared import create_base_application
from shared.di import injector
from shared.services import EnvironmentService, ShutdownService
from shared.tests import reset_di  # noqa


@pytest.fixture()
def env_service(reset_di):  # noqa
    injector.register(EnvironmentService, EnvironmentService)
    yield injector.get(EnvironmentService)


def test_create_base_application():
    flask_frontend = MagicMock()
    app = MagicMock()
    flask_frontend.create_application = ca = MagicMock(return_value=app)

    shutdown_service = MagicMock()
    get = MagicMock(return_value=shutdown_service)
    with patch("atexit.register") as register, patch(
        "shared.init_logging"
    ) as init_logging, patch.object(injector, "get", new=get) as iget:
        assert create_base_application(flask_frontend) == app

        print("", end="")  # simulate that the flushprint is tested
        register.assert_called_once()

        shutdown = register.call_args_list[0][0][0]
        shutdown()
        iget.assert_called_with(ShutdownService)
        shutdown_service.shutdown.assert_called_once()

        init_logging.assert_called_once()
        ca.assert_called_once()


def test_create_base_application_gunicorn(env_service):
    os.environ["SERVER_SOFTWARE"] = "gunicorn"
    env_service.cache = {}
    with patch("atexit.register"), patch("shared.init_logging") as init_logging:
        create_base_application(MagicMock())
        init_logging.assert_called()
        assert init_logging.call_args[0][0] == "gunicorn.error"
