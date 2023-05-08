from collections import defaultdict
from typing import Dict, Tuple, Union

from ..typing import Collection, Field, Fqfield, Fqid, Id, Model
from .key_strings import KEYSEPARATOR


def collectionfield_from_fqid_and_field(fqid: Fqid, field: Field) -> str:
    return f"{collection_from_fqid(fqid)}{KEYSEPARATOR}{field}"


def fqfield_from_fqid_and_field(fqid: Fqid, field: Field) -> Fqfield:
    return f"{fqid}{KEYSEPARATOR}{field}"


def fqid_from_fqfield(fqfield: Fqfield) -> Fqid:
    return collectionfield_and_fqid_from_fqfield(fqfield)[1]


def field_from_fqfield(fqfield: Fqfield) -> Field:
    return fqfield.split(KEYSEPARATOR)[2]


def field_from_collectionfield(collectionfield: str) -> Field:
    return collectionfield.split(KEYSEPARATOR)[1]


def id_from_fqid(fqid: Fqid) -> Id:
    return int(fqid.split(KEYSEPARATOR)[1])


def collectionfield_and_fqid_from_fqfield(fqfield: Fqfield) -> Tuple[str, Fqid]:
    parts = fqfield.split(KEYSEPARATOR)
    return f"{parts[0]}{KEYSEPARATOR}{parts[2]}", f"{parts[0]}{KEYSEPARATOR}{parts[1]}"


def collection_from_fqid(fqid: Fqid) -> Collection:
    return fqid.split(KEYSEPARATOR)[0]


def collection_and_id_from_fqid(fqid: Fqid) -> Tuple[Collection, Id]:
    s = fqid.split(KEYSEPARATOR)
    return s[0], int(s[1])


def collection_from_collectionfield(collectionfield: str) -> Collection:
    return collectionfield.split(KEYSEPARATOR)[0]


def fqid_from_collection_and_id(collection: Collection, id: Union[str, Id]) -> Fqid:
    return f"{collection}{KEYSEPARATOR}{id}"


def change_model_mapping(
    models: Dict[Fqid, Model]
) -> Dict[Collection, Dict[Id, Model]]:
    new: Dict[Collection, Dict[Id, Model]] = defaultdict(dict)
    for fqid, model in models.items():
        collection, id = collection_and_id_from_fqid(fqid)
        new[collection][id] = model
    return new
