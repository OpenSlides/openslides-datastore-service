import pytest

from shared.di import injector
from shared.util import reset_di  # noqa
from shared.util import META_DELETED
from writer.core import (
    RequestCreateEvent,
    RequestDeleteEvent,
    RequestRestoreEvent,
    RequestUpdateEvent,
)
from writer.core.db_events import (
    DbCreateEvent,
    DbDeleteEvent,
    DbDeleteFieldsEvent,
    DbRestoreEvent,
    DbUpdateEvent,
)
from writer.core.event_translator import EventTranslator, EventTranslatorService


@pytest.fixture()
def event_translator(reset_di):  # noqa
    injector.register(EventTranslator, EventTranslatorService)
    yield injector.get(EventTranslator)


@pytest.fixture()
def request_events():
    yield [
        RequestCreateEvent("a/1", {"a": 1}),
        RequestDeleteEvent("b/2"),
        RequestUpdateEvent("a/1", {"a": None, "b": [1, True]}),
        RequestRestoreEvent("b/2"),
    ]


def test_creation(event_translator):
    assert bool(event_translator)


def test_no_events(event_translator):
    db_events = event_translator.translate([])

    assert db_events == []


def test_translation_amount(event_translator, request_events):
    db_events = event_translator.translate(request_events)

    assert len(db_events) == 5


def test_translation_types(event_translator, request_events):
    db_events = event_translator.translate(request_events)

    assert isinstance(db_events[0], DbCreateEvent)
    assert isinstance(db_events[1], DbDeleteEvent)
    assert isinstance(db_events[2], DbUpdateEvent)
    assert isinstance(db_events[3], DbDeleteFieldsEvent)
    assert isinstance(db_events[4], DbRestoreEvent)


def test_translation_contents(event_translator, request_events):
    db_events = event_translator.translate(request_events)

    assert db_events[0].fqid == "a/1"
    assert db_events[0].field_data == {"a": 1, META_DELETED: False}
    assert db_events[1].fqid == "b/2"
    assert db_events[2].fqid == "a/1"
    assert db_events[2].field_data == {"b": [1, True]}
    assert db_events[3].fqid == "a/1"
    assert db_events[3].fields == ["a"]
    assert db_events[4].fqid == "b/2"


def test_translate_single_unknown_type(event_translator):
    with pytest.raises(RuntimeError):
        event_translator.translate_single(None)


def test_update_no_delete_fields_event(event_translator):
    update_event = RequestUpdateEvent("a/1", {"a": "some_value"})

    db_events = event_translator.translate_single(update_event)

    assert len(db_events) == 1
    assert isinstance(db_events[0], DbUpdateEvent)
