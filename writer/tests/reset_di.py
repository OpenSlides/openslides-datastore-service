import pytest

from writer.di import injector


@pytest.fixture(autouse=True)
def reset_di():
    injector.provider_map = {}
    yield
