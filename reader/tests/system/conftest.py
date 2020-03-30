import pytest

from reader.core import setup_di as core_setup_di
from reader.flask_frontend import FlaskFrontend
from shared.postgresql_backend import setup_di as postgresql_setup_di
from shared.services import setup_di as util_setup_di
from shared.tests import (  # noqa
    db_connection,
    db_cur,
    json_client,
    reset_db_data,
    reset_db_schema,
    reset_di,
    setup_db_connection,
)


@pytest.fixture(autouse=True)
def setup_di(reset_di):  # noqa
    util_setup_di()
    postgresql_setup_di()
    core_setup_di()


@pytest.fixture
def app(setup_di):
    application = FlaskFrontend.create_application()
    yield application
