from dataclasses import dataclass
from typing import List, Optional
from unittest.mock import MagicMock, patch

import pytest

from shared.typing import Collection, Field, Fqid, Id, Position
from shared.util import InvalidFormat, SelfValidatingDataclass


@dataclass
class A(SelfValidatingDataclass):
    fqid: Fqid
    collection: Collection
    field: Field
    id: Id
    position: Position


def test_simple():
    fqid = MagicMock(name="fqid")
    collection = MagicMock(name="collection")
    field = MagicMock(name="field")
    id = MagicMock(name="id")
    position = MagicMock(name="position")
    position.__le__.return_value = False

    with patch(
        "shared.util.self_validating_dataclass.assert_is_collection"
    ) as assert_is_collection, patch(
        "shared.util.self_validating_dataclass.assert_is_fqid"
    ) as assert_is_fqid, patch(
        "shared.util.self_validating_dataclass.assert_is_field"
    ) as assert_is_field, patch(
        "shared.util.self_validating_dataclass.assert_is_id"
    ) as assert_is_id:
        A(fqid, collection, field, id, position)

        assert_is_collection.assert_called_with(collection)
        assert_is_field.assert_called_with(field)
        assert_is_fqid.assert_called_with(fqid)
        assert_is_id.assert_called_with(str(id))
        position.__le__.assert_called_with(0)


@dataclass
class B(SelfValidatingDataclass):
    list: List[Fqid]
    position: Optional[Position]


def test_extended():
    fqid = MagicMock(name="fqid")
    position = MagicMock(name="position")
    position.__le__.return_value = True

    with patch(
        "shared.util.self_validating_dataclass.assert_is_fqid"
    ) as assert_is_fqid:
        with pytest.raises(InvalidFormat):
            B([fqid], position)

        assert_is_fqid.assert_called_with(fqid)
        position.__le__.assert_called_with(0)
