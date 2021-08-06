from dataclasses import dataclass

import pytest
import requests

from datastore.shared.services import EnvironmentService
from datastore.writer.flask_frontend.routes import TRUNCATE_DB_URL


@dataclass
class Env:
    writer: str
    reader: str


@pytest.fixture()
def env():
    env_service = EnvironmentService()

    writer_port = env_service.get("OPENSLIDES_DATASTORE_WRITER_PORT")
    reader_port = env_service.get("OPENSLIDES_DATASTORE_READER_PORT")

    yield Env(
        writer=f"http://localhost:{writer_port}",
        reader=f"http://localhost:{reader_port}",
    )


@pytest.fixture(autouse=True)
def truncate_db(env):
    response = requests.post(env.writer + TRUNCATE_DB_URL)
    assert response.status_code == 204
    yield
