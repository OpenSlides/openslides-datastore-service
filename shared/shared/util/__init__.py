from typing import Any

from ..typing import JSON, Collection, Field, Fqid, Id, Model, Position  # noqa
from .deleted_models_behaviour import DeletedModelsBehaviour  # noqa
from .exceptions import (  # noqa
    DatastoreException,
    InvalidFormat,
    ModelDoesNotExist,
    ModelExists,
    ModelLocked,
    ModelNotDeleted,
)
from .filter import And, Filter, FilterOperator, Not, Or  # noqa
from .key_transforms import (  # noqa
    build_fqid,
    collection_from_fqid,
    collectionfield_and_fqid_from_fqfield,
    collectionfield_from_fqid_and_field,
    field_from_collectionfield,
    fqfield_from_fqid_and_field,
)
from .key_types import (  # noqa
    KEY_TYPE,
    InvalidKeyFormat,
    assert_is_collection,
    assert_is_collectionfield,
    assert_is_field,
    assert_is_fqfield,
    assert_is_fqid,
    assert_is_id,
    assert_string,
    get_key_type,
)
from .self_validating_dataclass import SelfValidatingDataclass  # noqa
from .key_strings import META_FIELD_PREFIX, KEYSEPARATOR, META_DELETED, META_POSITION, is_reserved_field  # noqa


def get_exception_for_deleted_models_behaviour(
    fqid: str, get_deleted_models: DeletedModelsBehaviour
) -> DatastoreException:
    if get_deleted_models == DeletedModelsBehaviour.ONLY_DELETED:
        return ModelNotDeleted(fqid)
    else:
        return ModelDoesNotExist(fqid)


class BadCodingError(RuntimeError):
    """
    Should be thrown for errors that theoretically should never happen, except when the
    programmer fucked up.
    """

    pass
