from .exceptions import (  # noqa
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
from .read_database import ReadDatabase, DeletedModelsBehaviour  # noqa


def raise_exception_for_deleted_models_behaviour(fqid: str, get_deleted_models: DeletedModelsBehaviour) -> None:
    if get_deleted_models == DeletedModelsBehaviour.ONLY_DELETED:
        raise ModelNotDeleted(fqid)
    else:
        raise ModelDoesNotExist(fqid)
