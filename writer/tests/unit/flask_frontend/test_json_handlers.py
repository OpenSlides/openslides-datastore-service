from unittest.mock import MagicMock, patch

import pytest

from shared.di import injector
from shared.flask_frontend import InvalidRequest
from shared.tests import reset_di  # noqa
from shared.util import BadCodingError
from writer.core import Writer
from writer.flask_frontend.json_handlers import GetIdsHandler, WriteHandler


@pytest.fixture()
def writer(reset_di):  # noqa
    injector.register_as_singleton(Writer, MagicMock)
    yield injector.get(Writer)


@pytest.fixture()
def write_handler():
    yield WriteHandler()


@pytest.fixture()
def get_ids_handler():
    yield GetIdsHandler()


class TestWriteHandler:
    def test_wrong_schema(self, write_handler):
        with pytest.raises(InvalidRequest):
            write_handler.write(None)

    def test_corrct_schema(self, write_handler, writer):
        writer.write = w = MagicMock()
        event = MagicMock()
        write_handler.create_event = MagicMock(return_value=event)

        with patch("writer.flask_frontend.json_handlers.WriteRequest") as wr:
            write_handler.write(
                {
                    "user_id": -2,
                    "information": [None, True],
                    "locked_fields": {"some_string": 1},
                    "events": [
                        {"type": "create", "fqid": "some_fqid", "fields": {}},
                        {"type": "update", "fqid": "some_fqid", "fields": {}},
                        {"type": "delete", "fqid": "some_fqid"},
                        {"type": "restore", "fqid": "some_fqid"},
                    ],
                }
            )
            wr.assert_called_once()
            args = wr.call_args.args
            assert args == (
                [event, event, event, event],
                [None, True],
                -2,
                {"some_string": 1},
            )

        w.assert_called_once()

    def test_parse_events_create_event_type(self, write_handler):
        event = {"type": "create", "fields": ["not_a_dict"]}
        with pytest.raises(InvalidRequest):
            write_handler.parse_events([event])

    def test_parse_events_create_event_field_type(self, write_handler):
        event = {"type": "create", "fields": {1: "key_is_not_a_string"}}
        with pytest.raises(InvalidRequest):
            write_handler.parse_events([event])

    def test_parse_events_update_event_type(self, write_handler):
        event = {"type": "update", "fields": ["not_a_dict"]}
        with pytest.raises(InvalidRequest):
            write_handler.parse_events([event])

    def test_parse_events_update_event_field_type(self, write_handler):
        event = {"type": "update", "fields": {1: "key_is_not_a_string"}}
        with pytest.raises(InvalidRequest):
            write_handler.parse_events([event])

    def test_create_create_event(self, write_handler):
        fqid = MagicMock()
        fields = MagicMock()
        event = {"type": "create", "fqid": fqid, "fields": fields}
        with patch("writer.flask_frontend.json_handlers.RequestCreateEvent") as rce:
            rce.return_value = request_event = MagicMock()
            assert write_handler.create_event(event) == request_event
            assert rce.call_args.args == (fqid, fields,)

    def test_create_update_event(self, write_handler):
        fqid = MagicMock()
        fields = MagicMock()
        event = {"type": "update", "fqid": fqid, "fields": fields}
        with patch("writer.flask_frontend.json_handlers.RequestUpdateEvent") as rue:
            rue.return_value = request_event = MagicMock()
            assert write_handler.create_event(event) == request_event
            assert rue.call_args.args == (fqid, fields,)

    def test_create_delete_event(self, write_handler):
        fqid = MagicMock()
        event = {"type": "delete", "fqid": fqid}
        with patch("writer.flask_frontend.json_handlers.RequestDeleteEvent") as rde:
            rde.return_value = request_event = MagicMock()
            assert write_handler.create_event(event) == request_event
            assert rde.call_args.args == (fqid,)

    def test_create_restore_event(self, write_handler):
        fqid = MagicMock()
        event = {"type": "restore", "fqid": fqid}
        with patch("writer.flask_frontend.json_handlers.RequestRestoreEvent") as rre:
            rre.return_value = request_event = MagicMock()
            assert write_handler.create_event(event) == request_event
            assert rre.call_args.args == (fqid,)

    def test_create_unknown_event(self, write_handler):
        event = {"type": "unknwon", "fqid": "a/1"}
        with pytest.raises(BadCodingError):
            write_handler.create_event(event)


class TestGetIdsHandler:
    def test_wrong_schema(self, get_ids_handler):
        with pytest.raises(InvalidRequest):
            get_ids_handler.get_ids(None)

    def test_correct_schema(self, get_ids_handler, writer):
        writer.get_ids = gi = MagicMock()
        data = {"collection": "my_collection", "amount": -3}
        get_ids_handler.get_ids(data)
        gi.assert_called_once()
        assert gi.call_args.args == ("my_collection", -3,)
