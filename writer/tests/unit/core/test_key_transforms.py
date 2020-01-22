from writer.core import (
    collectionfield_from_fqid_and_field,
    fqfield_from_fqid_and_field,
    fqid_and_field_from_fqfield,
)


def test_collectionfield_from_fqid_and_field():
    fqid = "a/1"
    field = "f"

    assert collectionfield_from_fqid_and_field(fqid, field) == "a/f"


def test_fqid_and_field_from_fqfield():
    fqfield = "a/1/f"

    assert fqid_and_field_from_fqfield(fqfield) == ("a/1", "f")


def test_fqfield_from_fqid_and_field():
    fqid = "a/1"
    field = "f"

    assert fqfield_from_fqid_and_field(fqid, field) == "a/1/f"
