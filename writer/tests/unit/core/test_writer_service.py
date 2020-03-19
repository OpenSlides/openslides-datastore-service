from unittest.mock import MagicMock

import pytest

from shared.di import injector
from shared.tests import reset_di  # noqa
from writer.core import (
    Database,
    Messaging,
    OccLocker,
    RequestCreateEvent,
    RequestDeleteEvent,
    Writer,
    WriteRequest,
)
from writer.core.event_executor import EventExecutor
from writer.core.event_translator import EventTranslator
from writer.core.writer_service import WriterService


@pytest.fixture(autouse=True)
def provide_di(reset_di):  # noqa
    injector.register_as_singleton(Database, MagicMock)
    injector.register_as_singleton(OccLocker, lambda: MagicMock(unsafe=True))
    injector.register_as_singleton(EventTranslator, MagicMock)
    injector.register_as_singleton(EventExecutor, MagicMock)
    injector.register_as_singleton(Messaging, MagicMock)
    injector.register(Writer, WriterService)
    yield


@pytest.fixture()
def writer(provide_di):
    yield injector.get(Writer)


@pytest.fixture()
def database(provide_di):
    yield injector.get(Database)


@pytest.fixture()
def occ_locker(provide_di):
    yield injector.get(OccLocker)


@pytest.fixture()
def event_translator(provide_di):
    yield injector.get(EventTranslator)


@pytest.fixture()
def event_executor(provide_di):
    yield injector.get(EventExecutor)


@pytest.fixture()
def messaging(provide_di):
    yield injector.get(Messaging)


def test_writer_creation(writer):
    assert bool(writer)


def test_writer_distribution(writer, database, occ_locker, event_translator):
    events = [RequestCreateEvent("a/1", {"a": 1}), RequestDeleteEvent("b/2")]
    locked_fields = {
        "c/1": 3,
        "c/2/f": 4,
        "c/f": 5,
    }
    write_request = WriteRequest(events, {}, 1, locked_fields)
    event_translator.translate = MagicMock(return_value=[2, 3, 4])
    writer.propagate_updates = pu = MagicMock()

    writer.write(write_request)

    event_translator.translate.assert_called_with(events)
    database.get_context.assert_called()
    occ_locker.assert_fqid_positions.assert_called_with({"c/1": 3})
    occ_locker.assert_fqfield_positions.assert_called_with({"c/2/f": 4})
    occ_locker.assert_collectionfield_positions.assert_called_with({"c/f": 5})
    database.insert_events.assert_called_with([2, 3, 4], {}, 1)
    pu.assert_called_once()


def test_propagate_updates(writer, event_executor, messaging):
    writer.position = p = MagicMock()
    writer.db_events = dbe = MagicMock()
    event_executor.update = u = MagicMock()
    messaging.handle_events = he = MagicMock()

    writer.propagate_updates()

    u.assert_called_with(dbe, p)
    he.assert_called_with(dbe, p)


def test_writer_get_ids(writer, database):
    writer.get_ids("collection", 4)
    database.get_context.assert_called()
    database.reserve_next_ids.assert_called_with("collection", 4)
