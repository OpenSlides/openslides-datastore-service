from unittest.mock import MagicMock

import pytest

from shared.util import META_DELETED, BadCodingError
from writer.core.db_events import (
    BaseDbEvent,
    DbCreateEvent,
    DbDeleteEvent,
    DbDeleteFieldsEvent,
    DbListUpdateEvent,
    DbRestoreEvent,
    DbUpdateEvent,
)


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

    modified_fields = event.get_modified_fields()
    assert "my_key" in modified_fields


def test_db_list_update_event():
    fqid = MagicMock()
    value = MagicMock()
    add = {"my_key": value}
    remove = {"other_key": value}

    event = DbListUpdateEvent(fqid, add, remove)
    # init translated events
    event.translate_events({})

    assert event.fqid == fqid
    assert "my_key" in event.add
    assert "other_key" in event.remove

    modified_fields = event.get_modified_fields()
    assert "my_key" in modified_fields
    assert "other_key" in modified_fields


def test_db_list_update_event_get_translated_events_before_translate():
    event = DbListUpdateEvent(MagicMock(), {}, {})
    with pytest.raises(BadCodingError):
        event.get_translated_events()


def test_db_list_update_event_translate_events_empty_events():
    event = DbListUpdateEvent(MagicMock(), {}, {})
    with pytest.raises(BadCodingError):
        event.translate_events(MagicMock())


def test_db_list_update_event_double_translate_events():
    event = DbListUpdateEvent(MagicMock(), {}, {})
    event.calculate_updated_fields = MagicMock(return_value=[MagicMock(), MagicMock()])
    event.translate_events({})
    with pytest.raises(BadCodingError):
        event.translate_events({})


def test_db_delete_fields_event():
    fqid = MagicMock()
    field = MagicMock()

    event = DbDeleteFieldsEvent(fqid, [field])

    assert event.fqid == fqid
    assert event.fields == [field]
    assert event.get_modified_fields() == {field: None}


def test_db_delete_event():
    fqid = MagicMock()
    field = MagicMock()

    event = DbDeleteEvent(fqid)
    event.fields = [field]

    assert event.fqid == fqid
    assert event.get_modified_fields() == {field: None}


def test_db_delete_event_set_modified_fields():
    field = MagicMock()

    event = DbDeleteEvent(None)
    event.set_modified_fields([field])

    assert event.get_modified_fields() == {field: None}


def test_db_restore_event():
    fqid = MagicMock()
    field = MagicMock()

    event = DbRestoreEvent(fqid)
    event.fields = [field]

    assert event.fqid == fqid
    assert event.get_modified_fields() == {field: None}


def test_db_restore_event_set_modified_fields():
    field = MagicMock()

    event = DbRestoreEvent(None)
    event.set_modified_fields([field])

    assert event.get_modified_fields() == {field: None}
