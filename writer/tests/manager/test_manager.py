import pytest
from typing import Iterator
from writer.manager import Manager

@pytest.fixture()
def manager() -> Iterator[Manager]:
    manager = Manager()
    yield manager

def test_manager_creation():
    assert Manager()
