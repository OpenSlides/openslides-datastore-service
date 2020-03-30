from typing import Any


META_FIELD_PREFIX = "meta"
KEYSEPARATOR = "/"
META_DELETED = f"{META_FIELD_PREFIX}_deleted"
META_POSITION = f"{META_FIELD_PREFIX}_position"


def is_reserved_field(field: Any) -> bool:
    return isinstance(field, str) and field.startswith(META_FIELD_PREFIX)
