from unittest.mock import MagicMock, patch

import pytest

from tests.reset_di import reset_di  # noqa
from writer.di import injector
from writer.shared import EnvironmentService
from writer.shared.environment_service import EnvironmentVariableMissing


@pytest.fixture()
def environment_service(reset_di):  # noqa
    injector.register(EnvironmentService, EnvironmentService)
    yield injector.get(EnvironmentService)


def test_environment_service_creation(environment_service):
    assert bool(environment_service)


def test_ensure_cache_not_in_cache(environment_service):
    key = MagicMock()
    environment_service.cache = {}
    with patch("writer.shared.environment_service.os.environ.get") as get:
        get.return_value = v = MagicMock()

        environment_service.ensure_cache(key)

        assert environment_service.cache[key] == v
        get.assert_called_once()


def test_ensure_cache_found(environment_service):
    key = MagicMock()
    environment_service.cache = {key: "value"}
    with patch("writer.shared.environment_service.os.environ.get") as get:
        environment_service.ensure_cache(key)

        assert get.call_count == 0


def test_try_get_in_cache(environment_service):
    key = MagicMock()
    value = MagicMock()
    environment_service.cache = {key: value}
    environment_service.ensure_cache = ec = MagicMock()

    assert environment_service.try_get(key) == value
    ec.assert_called_once()


def test_try_get_not_in_cache(environment_service):
    key = MagicMock()
    environment_service.cache = {}
    environment_service.ensure_cache = ec = MagicMock()

    assert environment_service.try_get(key) is None
    ec.assert_called_once()


def test_get_in_cache(environment_service):
    key = MagicMock()
    value = MagicMock()
    environment_service.cache = {key: value}
    environment_service.ensure_cache = ec = MagicMock()

    assert environment_service.get(key) == value
    ec.assert_called_once()


def test_get_not_in_cache(environment_service):
    key = MagicMock()
    environment_service.cache = {}
    environment_service.ensure_cache = ec = MagicMock()

    with pytest.raises(EnvironmentVariableMissing):
        environment_service.get(key)
    ec.assert_called_once()


def test_set(environment_service):
    key = MagicMock()
    value = MagicMock()

    environment_service.set(key, value)

    assert environment_service.cache[key] == value
