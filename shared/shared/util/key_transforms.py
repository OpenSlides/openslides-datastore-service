from typing import Tuple

from .key_strings import KEYSEPARATOR


def collectionfield_from_fqid_and_field(fqid: str, field: str) -> str:
    return f"{collection_from_fqid(fqid)}{KEYSEPARATOR}{field}"


def fqfield_from_fqid_and_field(fqid: str, field: str) -> str:
    return f"{fqid}{KEYSEPARATOR}{field}"


def fqid_from_fqfield(fqfield: str) -> str:
    return collectionfield_and_fqid_from_fqfield(fqfield)[1]


def field_from_fqfield(fqfield: str) -> str:
    return fqfield.split(KEYSEPARATOR)[2]


def field_from_collectionfield(collectionfield: str) -> str:
    return collectionfield.split(KEYSEPARATOR)[1]


def id_from_fqid(fqid: str) -> int:
    return int(fqid.split(KEYSEPARATOR)[1])


def collectionfield_and_fqid_from_fqfield(fqfield: str) -> Tuple[str, str]:
    parts = fqfield.split(KEYSEPARATOR)
    return f"{parts[0]}{KEYSEPARATOR}{parts[2]}", f"{parts[0]}{KEYSEPARATOR}{parts[1]}"


def collection_from_fqid(fqid: str) -> str:
    return fqid.split(KEYSEPARATOR)[0]


def collection_and_id_from_fqid(fqid: str) -> Tuple[str, int]:
    s = fqid.split(KEYSEPARATOR)
    return s[0], int(s[1])


def build_fqid(collection: str, id: str) -> str:
    return f"{collection}{KEYSEPARATOR}{id}"
