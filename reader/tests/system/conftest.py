import pytest

from reader.core import setup_di as core_setup_di
from reader.flask_frontend import FlaskFrontend
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
    core_setup_di()


@pytest.fixture
def app(setup_di):
    application = FlaskFrontend.create_application()
    yield application
