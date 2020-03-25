from unittest.mock import MagicMock, patch

import pytest

from shared.core import InvalidFormat, InvalidKeyFormat
from writer.core import (
    RequestCreateEvent,
    RequestDeleteEvent,
    RequestRestoreEvent,
    RequestUpdateEvent,
    WriteRequest,
)
from writer.core.write_request import assert_no_special_field


def get_dummy_request_events():
    return [RequestCreateEvent("c/1", {"a": 1})]


def test_no_events():
    with pytest.raises(InvalidFormat):
        WriteRequest([], {}, 1, {})


def test_wrong_locked_field_format():
    locked_fields = {"_no_valid_key": 932}
    with pytest.raises(InvalidKeyFormat):
        WriteRequest(get_dummy_request_events(), {}, 1, locked_fields)


def test_wrong_locked_field_position_1():
    locked_fields = {"collection/field": 0}
    with pytest.raises(InvalidFormat):
        WriteRequest(get_dummy_request_events(), {}, 1, locked_fields)


def test_wrong_locked_field_position_2():
    locked_fields = {"collection/field": -492}
    with pytest.raises(InvalidFormat):
        WriteRequest(get_dummy_request_events(), {}, 1, locked_fields)


def test_parsing_locked_fields():
    locked_fields = {
        "collection/field": 1,
        "collection/29": 2,
        "collection/49/field": 3,
    }
    wr = WriteRequest(get_dummy_request_events(), {}, 1, locked_fields)

    assert wr.locked_collectionfields["collection/field"] == 1
    assert wr.locked_fqids["collection/29"] == 2
    assert wr.locked_fqfields["collection/49/field"] == 3


def test_create_update_fqid():
    for event in (RequestCreateEvent, RequestUpdateEvent):
        with pytest.raises(InvalidKeyFormat):
            event("_no_fqid_here", {"f": 1})


def test_update_no_fields():
    with pytest.raises(InvalidFormat):
        RequestUpdateEvent("c/1", {})


def test_create_update_wrong_field_format():
    for event in (RequestCreateEvent, RequestUpdateEvent):
        with pytest.raises(InvalidKeyFormat):
            event("c/1", {"_not_valid": "value"})


def test_create_update_reserved_field():
    for event in (RequestCreateEvent, RequestUpdateEvent):
        with pytest.raises(InvalidFormat) as e:
            event("meta_some_field", {"valid": "value"})
        assert "meta_some_field" in e.value.msg


def test_delete_restore_fqid():
    for event in (RequestDeleteEvent, RequestRestoreEvent):
        with pytest.raises(InvalidKeyFormat):
            event("_no_fqid_here")


def test_assert_no_special_field():
    with patch("writer.core.write_request.is_reserved_field") as irf:
        irf.return_value = True
        with pytest.raises(InvalidFormat):
            assert_no_special_field(MagicMock())


def test_create_prune_none():
    field_data = {"none": None}

    event = RequestCreateEvent("a/1", field_data)

    assert event.fields == {}
