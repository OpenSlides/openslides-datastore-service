from unittest.mock import MagicMock

import pytest

from datastore.migrations import BaseEvent
from datastore.migrations.migration_keyframes import (
    DatabaseMigrationKeyframeModifier,
    InitialMigrationKeyframeModifier,
    MigrationKeyframeAccessor,
    MigrationKeyframeModifier,
)
from datastore.shared.util import BadCodingError


def test_not_implemented():
    accessor = MigrationKeyframeAccessor(
        MagicMock(), MagicMock(), MagicMock(), MagicMock()
    )
    with pytest.raises(NotImplementedError):
        accessor._fetch_model(MagicMock())
    with pytest.raises(NotImplementedError):
        accessor.get_all_ids_for_collection(MagicMock())
    with pytest.raises(NotImplementedError):
        accessor.apply_event(MagicMock())

    modifier = MigrationKeyframeModifier(
        MagicMock(), MagicMock(), MagicMock(), MagicMock()
    )
    with pytest.raises(NotImplementedError):
        modifier._create_model(MagicMock(), MagicMock())
    with pytest.raises(NotImplementedError):
        modifier._update_model(MagicMock(), MagicMock())
    with pytest.raises(NotImplementedError):
        modifier.move_to_next_position()


def test_bad_event():
    class MyEvent(BaseEvent):
        pass

    modifier = MigrationKeyframeModifier(
        MagicMock(), MagicMock(), MagicMock(), MagicMock()
    )
    modifier._fetch_model = MagicMock()  # type: ignore
    with pytest.raises(BadCodingError):
        modifier.apply_event(MyEvent("a/1", {}))


def test_initial_keyframe_modifier_position():
    with pytest.raises(BadCodingError):
        InitialMigrationKeyframeModifier(MagicMock(), 1, MagicMock(), MagicMock())


def test_database_keyframe_modifier_position():
    with pytest.raises(BadCodingError):
        DatabaseMigrationKeyframeModifier(
            MagicMock(), 0, MagicMock(), MagicMock(), MagicMock()
        )


def test_database_keyframe_modifier_non_persistent():
    modifier = DatabaseMigrationKeyframeModifier(
        MagicMock(), 1, MagicMock(), MagicMock(), False
    )
    with pytest.raises(BadCodingError):
        modifier.move_to_next_position()


def test_database_keyframe_modifier_no_keyframe():
    connection = MagicMock()
    connection.query_single_value = MagicMock(return_value=None)
    with pytest.raises(BadCodingError):
        DatabaseMigrationKeyframeModifier(
            connection, 1, MagicMock(), MagicMock(), False
        )
