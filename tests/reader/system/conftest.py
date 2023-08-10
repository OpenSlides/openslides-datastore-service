import pytest

from datastore.reader import setup_di as reader_setup_di
from datastore.reader.flask_frontend import FlaskFrontend
from datastore.shared.postgresql_backend import setup_di as postgresql_setup_di
from datastore.shared.services import setup_di as util_setup_di
from tests import (  # noqa
    client,
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
    reader_setup_di()


@pytest.fixture()
def app(setup_di):
    application = FlaskFrontend.create_application()
    yield application
