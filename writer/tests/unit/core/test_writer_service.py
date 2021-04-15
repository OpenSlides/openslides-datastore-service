import threading
from threading import Thread
from unittest.mock import MagicMock

import pytest

from shared.di import injector
from shared.services import EnvironmentService
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
    injector.register(EnvironmentService, EnvironmentService)
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


def test_writer_distribution(
    writer, database, occ_locker, event_translator, event_executor, messaging
):
    events = [RequestCreateEvent("a/1", {"a": 1}), RequestDeleteEvent("b/2")]
    locked_fields = {
        "c/1": 3,
        "c/2/f": 4,
        "c/f": 5,
    }
    write_request = WriteRequest(events, {}, 1, locked_fields)
    event_translator.translate = MagicMock(return_value=[2, 3, 4])
    event_executor.update = eeu = MagicMock()
    messaging.handle_events = he = MagicMock()

    writer.write([write_request])

    event_translator.translate.assert_called_with(events)
    database.get_context.assert_called()
    occ_locker.assert_fqid_positions.assert_called_with({"c/1": 3})
    occ_locker.assert_fqfield_positions.assert_called_with({"c/2/f": 4})
    occ_locker.assert_collectionfield_positions.assert_called_with({"c/f": 5})
    database.insert_events.assert_called_with([2, 3, 4], {}, 1)
    eeu.assert_called_once()
    he.assert_called_once()


def test_writer_reserve_ids(writer, database):
    writer.reserve_ids("collection", 4)
    database.get_context.assert_called()
    database.reserve_next_ids.assert_called_with("collection", 4)


def test_writer_truncate_db(writer, database):
    writer.truncate_db()
    database.get_context.assert_called()
    database.truncate_db.assert_called()


def test_writer_single_thread(writer):
    writer.locks = [threading.Lock(), threading.Lock()]
    writer.locks[0].acquire()
    writer.current_lock = 0
    writer.position = 0

    def wait_for_lock(*args, **kwargs):
        lock = writer.locks[writer.current_lock]
        writer.current_lock += 1
        lock.acquire()
        lock.release()

    writer.event_translator = MagicMock()
    writer.messaging = MagicMock()
    writer.write_with_database_context = MagicMock(side_effect=wait_for_lock)

    thread1 = Thread(target=writer.write, args=[[MagicMock()]])
    thread1.start()
    thread2 = Thread(target=writer.write, args=[[MagicMock()]])
    thread2.start()

    thread1.join(0.5)
    assert thread1.is_alive()
    assert thread2.is_alive()

    assert writer.locks[0].locked()
    assert not writer.locks[1].locked()

    writer.locks[0].release()
    thread1.join(0.05)
    thread2.join(0.05)
    assert not thread1.is_alive()
    assert not thread2.is_alive()
