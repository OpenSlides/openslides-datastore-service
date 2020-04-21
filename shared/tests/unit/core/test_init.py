from unittest.mock import MagicMock
import pytest
from shared.core import (DeletedModelsBehaviour, ModelDoesNotExist, ModelNotDeleted,
    raise_exception_for_deleted_models_behaviour)


def test_raise_exception_for_deleted_models_behaviour_no_deleted():
    with pytest.raises(ModelDoesNotExist):
        raise_exception_for_deleted_models_behaviour(MagicMock(), DeletedModelsBehaviour.NO_DELETED)


def test_raise_exception_for_deleted_models_behaviour_only_deleted():
    with pytest.raises(ModelNotDeleted):
        raise_exception_for_deleted_models_behaviour(MagicMock(), DeletedModelsBehaviour.ONLY_DELETED)