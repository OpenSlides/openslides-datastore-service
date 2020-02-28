from typing import Tuple

from writer.shared import KEYSEPARATOR


def collectionfield_from_fqid_and_field(fqid: str, field: str) -> str:
    parts = fqid.split(KEYSEPARATOR)
    return f"{parts[0]}{KEYSEPARATOR}{field}"


def fqfield_from_fqid_and_field(fqid: str, field: str) -> str:
    return f"{fqid}{KEYSEPARATOR}{field}"


def field_from_collectionfield(collectionfield: str) -> str:
    return collectionfield.split(KEYSEPARATOR)[1]


def collectionfield_and_fqid_from_fqfield(collectionfield: str) -> Tuple[str, str]:
    parts = collectionfield.split(KEYSEPARATOR)
    return f"{parts[0]}{KEYSEPARATOR}{parts[2]}", f"{parts[0]}{KEYSEPARATOR}{parts[1]}"
