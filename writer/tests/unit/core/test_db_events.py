from unittest.mock import MagicMock

import pytest

from writer.core import (
    DbCreateEvent,
    DbDeleteEvent,
    DbDeleteFieldsEvent,
    DbRestoreEvent,
    DbUpdateEvent,
)
from writer.core.db_events import BaseDbEvent
from writer.shared import META_DELETED


def test_base_db_event_get_modified_fields():
    with pytest.raises(NotImplementedError):
        BaseDbEvent("a/1").get_modified_fields()


def test_db_create_event():
    fqid = MagicMock()
    value = MagicMock()
    field_data = {"my_key": value}

    event = DbCreateEvent(fqid, field_data)

    assert event.fqid == fqid
    assert "my_key" in event.field_data
    assert META_DELETED in event.field_data

    fields = event.get_fields()
    assert "my_key" in fields
    assert META_DELETED in fields

    modified_fields = event.get_modified_fields()
    assert "my_key" in modified_fields
    assert META_DELETED in modified_fields


def test_db_update_event():
    fqid = MagicMock()
    value = MagicMock()
    field_data = {"my_key": value}

    event = DbUpdateEvent(fqid, field_data)

    assert event.fqid == fqid
    assert "my_key" in event.field_data

    fields = event.get_fields()
    assert "my_key" in fields

    modified_fields = event.get_modified_fields()
    assert "my_key" in modified_fields


def test_db_delete_fields_event():
    fqid = MagicMock()
    fields = MagicMock()

    event = DbDeleteFieldsEvent(fqid, fields)

    assert event.fqid == fqid
    assert event.fields == fields
    assert event.get_modified_fields() == fields


def test_db_delete_event():
    fqid = MagicMock()

    event = DbDeleteEvent(fqid)
    event.modified_fields = fields = MagicMock()

    assert event.fqid == fqid
    assert event.get_modified_fields() == fields


def test_db_delete_event_set_modified_fields():
    fields = MagicMock()

    event = DbDeleteEvent(None)
    event.set_modified_fields(fields)

    assert event.get_modified_fields() == fields


def test_db_restore_event():
    fqid = MagicMock()

    event = DbRestoreEvent(fqid)
    event.modified_fields = fields = MagicMock()

    assert event.fqid == fqid
    assert event.get_modified_fields() == fields


def test_db_restore_event_set_modified_fields():
    fields = MagicMock()

    event = DbRestoreEvent(None)
    event.set_modified_fields(fields)

    assert event.get_modified_fields() == fields
