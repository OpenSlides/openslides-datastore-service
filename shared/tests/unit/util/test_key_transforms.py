from shared.util import (
    build_fqid,
    collection_from_fqid,
    collectionfield_and_fqid_from_fqfield,
    collectionfield_from_fqid_and_field,
    field_from_collectionfield,
    fqfield_from_fqid_and_field,
)
from shared.util.key_transforms import field_from_fqfield, fqid_from_fqfield


def test_collectionfield_from_fqid_and_field():
    fqid = "a/1"
    field = "f"

    assert collectionfield_from_fqid_and_field(fqid, field) == "a/f"


def test_fqfield_from_fqid_and_field():
    fqid = "a/1"
    field = "f"

    assert fqfield_from_fqid_and_field(fqid, field) == "a/1/f"


def test_fqid_from_fqfield():
    fqfield = "a/1/f"

    assert fqid_from_fqfield(fqfield) == "a/1"


def test_field_from_fqfield():
    fqfield = "a/1/f"

    assert field_from_fqfield(fqfield) == "f"


def test_field_from_collectionfield():
    collectionfield = "a/f"

    assert field_from_collectionfield(collectionfield) == "f"


def test_collectionfield_and_fqid_from_fqfield():
    fqfield = "a/1/f"

    assert collectionfield_and_fqid_from_fqfield(fqfield) == ("a/f", "a/1")


def test_collection_from_fqid():
    fqid = "a/1"

    assert collection_from_fqid(fqid) == "a"


def test_build_fqid():
    collection = "collection"
    id = 1

    assert build_fqid(collection, id) == "collection/1"
