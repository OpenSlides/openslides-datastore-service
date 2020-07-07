from ..typing import JSON, Collection, Field, Fqid, Id, Model, Position  # noqa
from .deleted_models_behaviour import DeletedModelsBehaviour  # noqa
from .exceptions import (  # noqa
    BadCodingError,
    DatastoreException,
    InvalidFormat,
    ModelDoesNotExist,
    ModelExists,
    ModelLocked,
    ModelNotDeleted,
)
from .filter import And, Filter, FilterOperator, Not, Or  # noqa
from .key_strings import (  # noqa
    KEYSEPARATOR,
    META_DELETED,
    META_FIELD_PREFIX,
    META_POSITION,
    is_reserved_field,
)
from .key_transforms import (  # noqa
    build_fqid,
    collection_from_fqid,
    collectionfield_and_fqid_from_fqfield,
    collectionfield_from_fqid_and_field,
    field_from_collectionfield,
    fqfield_from_fqid_and_field,
    id_from_fqid,
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
from .logging import logger  # noqa
from .self_validating_dataclass import SelfValidatingDataclass  # noqa


ALL_TABLES = (
    "positions",
    "events",
    "models_lookup",
    "id_sequences",
    "collectionfields",
    "events_to_collectionfields",
    "models",
)


def get_exception_for_deleted_models_behaviour(
    fqid: str, get_deleted_models: DeletedModelsBehaviour
) -> DatastoreException:
    if get_deleted_models == DeletedModelsBehaviour.ONLY_DELETED:
        return ModelNotDeleted(fqid)
    else:
        return ModelDoesNotExist(fqid)
