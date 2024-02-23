import pytest

from datastore.shared.postgresql_backend import setup_di as postgresql_setup_di
from datastore.shared.services import setup_di as util_setup_di
from datastore.writer import setup_di as writer_setup_di
from datastore.writer.redis_backend import setup_di as redis_setup_di
from tests import (  # noqa
    db_connection,
    db_cur,
    reset_db_data,
    reset_db_schema,
    reset_di,
    setup_db_connection,
)


# Application


@pytest.fixture(autouse=True)
def setup_di(reset_di):  # noqa
    util_setup_di()
    postgresql_setup_di()
    redis_setup_di()
    writer_setup_di()
