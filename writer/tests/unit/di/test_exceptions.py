from typing import Protocol

import pytest

from writer.di.exceptions import DependencyNotFound


class MyProtocol(Protocol):
    pass


def test_dependency_not_found_arguments():
    with pytest.raises(DependencyNotFound) as e:
        raise DependencyNotFound(MyProtocol)
    assert e.value.protocol == MyProtocol
