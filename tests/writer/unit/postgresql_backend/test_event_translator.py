from unittest.mock import MagicMock

import pytest

from datastore.shared.di import injector
from datastore.shared.services import ReadDatabase
from datastore.shared.util import BadCodingError
from datastore.writer.core import (
    RequestCreateEvent,
    RequestDeleteEvent,
    RequestRestoreEvent,
    RequestUpdateEvent,
)
from datastore.writer.postgresql_backend import (
    DbCreateEvent,
    DbDeleteEvent,
    DbDeleteFieldsEvent,
    DbRestoreEvent,
    DbUpdateEvent,
)
from datastore.writer.postgresql_backend.event_translator import (
    EventTranslator,
    EventTranslatorService,
)
from tests import reset_di  # noqa


@pytest.fixture()
def event_translator(reset_di):  # noqa
    injector.register_as_singleton(ReadDatabase, MagicMock)
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


def test_translation_types(event_translator, request_events):
    db_events = [event_translator.translate(event) for event in request_events]

    assert isinstance(db_events[0][0], DbCreateEvent)
    assert isinstance(db_events[1][0], DbDeleteEvent)
    assert isinstance(db_events[2][0], DbUpdateEvent)
    assert isinstance(db_events[2][1], DbDeleteFieldsEvent)
    assert isinstance(db_events[3][0], DbRestoreEvent)


def test_translation_contents(event_translator, request_events):
    db_events = [event_translator.translate(event) for event in request_events]

    assert db_events[0][0].fqid == "a/1"
    assert db_events[0][0].field_data == {"a": 1}
    assert db_events[1][0].fqid == "b/2"
    assert db_events[2][0].fqid == "a/1"
    assert db_events[2][0].field_data == {"b": [1, True]}
    assert db_events[2][1].fqid == "a/1"
    assert db_events[2][1].fields == ["a"]
    assert db_events[3][0].fqid == "b/2"


def test_translate_single_unknown_type(event_translator):
    with pytest.raises(BadCodingError):
        event_translator.translate(None)


def test_update_no_delete_fields_event(event_translator):
    update_event = RequestUpdateEvent("a/1", {"a": "some_value"})

    db_events = event_translator.translate(update_event)

    assert len(db_events) == 1
    assert isinstance(db_events[0], DbUpdateEvent)
