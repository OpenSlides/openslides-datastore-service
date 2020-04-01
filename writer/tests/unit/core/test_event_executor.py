from unittest.mock import MagicMock

import pytest

from shared.core import ReadDatabase
from shared.di import injector
from shared.tests import reset_di  # noqa
from shared.util import META_POSITION, BadCodingError
from writer.core import (
    DbCreateEvent,
    DbDeleteEvent,
    DbDeleteFieldsEvent,
    DbRestoreEvent,
    DbUpdateEvent,
)
from writer.core.event_executor import MODEL_STATUS, EventExecutor, EventExecutorService


@pytest.fixture(autouse=True)
def provide_di(reset_di):  # noqa
    injector.register_as_singleton(ReadDatabase, MagicMock)
    injector.register(EventExecutor, EventExecutorService)
    yield


@pytest.fixture()
def event_executor(provide_di):
    yield injector.get(EventExecutor)


@pytest.fixture()
def read_database(provide_di):
    yield injector.get(ReadDatabase)


def test_event_executor_creation(event_executor):
    assert bool(event_executor)


def test_update(event_executor):
    events = MagicMock()
    position = MagicMock()
    models = MagicMock()
    event_executor.get_models = gm = MagicMock(return_value=models)
    event_executor.execute_events = ee = MagicMock()
    event_executor.restore_models = rm = MagicMock()
    event_executor.add_position = ap = MagicMock()
    event_executor.write_back = wb = MagicMock()

    event_executor.update(events, position)

    assert event_executor.events == events
    assert event_executor.position == position
    assert event_executor.models == models
    assert event_executor.model_status == {}
    gm.assert_called_once()
    ee.assert_called_once()
    rm.assert_called_once()
    ap.assert_called_once()
    wb.assert_called_once()


def test_get_many(event_executor, read_database):
    event1 = MagicMock()
    fqid1 = MagicMock()
    event1.fqid = fqid1
    event2 = MagicMock()
    event2.fqid = fqid1
    event3 = MagicMock()
    fqid2 = MagicMock()
    event3.fqid = fqid2
    event_executor.events = [event1, event2, event3]
    models = MagicMock()
    read_database.get_many = gm = MagicMock(return_value=models)

    assert event_executor.get_models() == models

    assert gm.call_count == 1
    args = gm.call_args.args[0]
    assert (args == [fqid1, fqid2]) or (args == [fqid2, fqid1])  # order not given


def test_execute_create_event(event_executor):
    event = MagicMock(spec=DbCreateEvent)
    event.fqid = fqid = MagicMock()
    event.field_data = field_data = MagicMock()
    event_executor.models = {fqid: MagicMock()}
    event_executor.model_status = {fqid: MagicMock()}

    event_executor.execute_event(event)

    assert event_executor.models[fqid] == field_data
    assert event_executor.model_status[fqid] == MODEL_STATUS.WRITE


def test_execute_restore_event(event_executor, read_database):
    event = MagicMock(spec=DbRestoreEvent)
    event.fqid = fqid = MagicMock()
    event_executor.models = {fqid: "here is a model!"}
    event_executor.model_status = {fqid: MODEL_STATUS.WRITE}

    event_executor.execute_event(event)

    assert fqid not in event_executor.models
    assert event_executor.model_status[fqid] == MODEL_STATUS.RESTORE


def test_execute_update_event(event_executor):
    event = MagicMock(spec=DbUpdateEvent)
    event.fqid = fqid = MagicMock()
    event.field_data = {"existing": "new", "new": "value"}
    event_executor.models = {fqid: {"not_touched": "old", "existing": "old"}}
    event_executor.model_status = {fqid: MagicMock()}

    event_executor.execute_event(event)

    assert event_executor.models[fqid] == {
        "not_touched": "old",
        "existing": "new",
        "new": "value",
    }
    assert event_executor.model_status[fqid] == MODEL_STATUS.WRITE


def test_execute_delete_fields_event(event_executor):
    event = MagicMock(spec=DbDeleteFieldsEvent)
    event.fqid = fqid = MagicMock()
    event.fields = ["b", "b", "c"]
    event_executor.models = {fqid: {"a": 1, "b": 2, "c": 3}}
    event_executor.model_status = {fqid: MagicMock()}

    event_executor.execute_event(event)

    assert event_executor.models[fqid] == {"a": 1}
    assert event_executor.model_status[fqid] == MODEL_STATUS.WRITE


def test_execute_delete_event(event_executor):
    event = MagicMock(spec=DbDeleteEvent)
    event.fqid = fqid = MagicMock()
    event_executor.models = {fqid: MagicMock()}
    event_executor.model_status = {fqid: MagicMock()}

    event_executor.execute_event(event)

    assert fqid not in event_executor.models
    assert event_executor.model_status[fqid] == MODEL_STATUS.DELETE


def test_execute_event_unknwon_event(event_executor):
    event = MagicMock()
    with pytest.raises(BadCodingError):
        event_executor.execute_event(event)


def test_execute_events_skip_write_after_delete_or_restore(event_executor):
    for initial_event_class in (DbDeleteEvent, DbRestoreEvent):
        fqid = MagicMock()
        initial_event = MagicMock(spec=initial_event_class)
        update_event = MagicMock(spec=DbUpdateEvent)
        delete_fields_event = MagicMock(spec=DbDeleteFieldsEvent)
        create_event = MagicMock(spec=DbCreateEvent)
        initial_event.fqid = (
            update_event.fqid
        ) = delete_fields_event.fqid = create_event.fqid = fqid
        event_executor.events = [
            initial_event,
            update_event,
            delete_fields_event,
            create_event,
        ]

        original_execute_event = event_executor.execute_event
        event_executor.execute_event = ee = MagicMock(
            side_effect=original_execute_event
        )

        event_executor.models = {fqid: MagicMock()}
        event_executor.model_status = {fqid: MagicMock()}

        event_executor.execute_events()

        ee.assert_called_with(initial_event)
        assert fqid not in event_executor.models
        assert event_executor.model_status[fqid] in (
            MODEL_STATUS.DELETE,
            MODEL_STATUS.RESTORE,
        )


def test_execute_events_change_model_status(event_executor):
    # test, deleted->restore and restore->deleted without calling execute_event
    for A in (DbRestoreEvent, DbDeleteEvent):
        fqid = MagicMock()
        event = MagicMock(spec=A)
        event.fqid = fqid
        event_executor.events = [event]
        event_executor.execute_event = ee = MagicMock()
        if A == DbRestoreEvent:
            event_executor.model_status = {fqid: MODEL_STATUS.DELETE}
        else:
            event_executor.model_status = {fqid: MODEL_STATUS.RESTORE}

        event_executor.execute_events()

        assert ee.call_count == 0
        if A == DbRestoreEvent:
            assert event_executor.model_status[fqid] == MODEL_STATUS.RESTORE
        else:
            assert event_executor.model_status[fqid] == MODEL_STATUS.DELETE


def test_restore_models(event_executor):
    fqid_1 = MagicMock()
    fqid_2 = MagicMock()
    event_executor.model_status = {
        fqid_1: MODEL_STATUS.RESTORE,
        fqid_2: MODEL_STATUS.RESTORE,
        MagicMock(): MODEL_STATUS.WRITE,
        MagicMock(): MODEL_STATUS.DELETE,
    }
    event_executor.models = {}
    restored_model = MagicMock()
    event_executor.build_model_ignore_deleted = bdm = MagicMock(
        return_value=restored_model
    )

    event_executor.restore_models()

    assert bdm.call_count == 2
    assert event_executor.models[fqid_1] == restored_model
    assert event_executor.models[fqid_2] == restored_model
    assert event_executor.model_status[fqid_1] == MODEL_STATUS.WRITE
    assert event_executor.model_status[fqid_2] == MODEL_STATUS.WRITE


def test_build_model_ignore_deleted(event_executor, read_database):
    model = MagicMock()
    fqid = MagicMock()
    read_database.build_model_ignore_deleted = bdm = MagicMock(return_value=model)

    assert event_executor.build_model_ignore_deleted(fqid) == model
    bdm.assert_called_with(fqid)


def test_add_position(event_executor):
    event_executor.models = {1: {}, 2: {}}
    event_executor.position = position = MagicMock()

    event_executor.add_position()

    assert event_executor.models[1][META_POSITION] == position
    assert event_executor.models[2][META_POSITION] == position


def test_write_back(event_executor, read_database):
    deleted_1 = MagicMock()
    deleted_2 = MagicMock()
    changed_1 = MagicMock()
    changed_1_data = MagicMock()
    changed_2 = MagicMock()
    changed_2_data = MagicMock()
    event_executor.model_status = {
        deleted_1: MODEL_STATUS.DELETE,
        deleted_2: MODEL_STATUS.DELETE,
        changed_1: MODEL_STATUS.WRITE,
        changed_2: MODEL_STATUS.WRITE,
    }
    event_executor.models = models = {
        changed_1: changed_1_data,
        changed_2: changed_2_data,
    }
    read_database.create_or_update_models = coum = MagicMock()
    read_database.delete_models = dm = MagicMock()

    event_executor.write_back()

    coum.assert_called_with(models)
    dm.assert_called_with([deleted_1, deleted_2])
