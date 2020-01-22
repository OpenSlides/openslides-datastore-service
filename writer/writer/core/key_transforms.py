from writer.shared import KEYSEPARATOR


def collectionfield_from_fqid_and_field(fqid, field):
    parts = fqid.split(KEYSEPARATOR)
    return f"{parts[0]}{KEYSEPARATOR}{field}"


def fqid_and_field_from_fqfield(fqfield):
    parts = fqfield.split(KEYSEPARATOR)
    return f"{parts[0]}{KEYSEPARATOR}{parts[1]}", parts[2]


def fqfield_from_fqid_and_field(fqid, field):
    return f"{fqid}{KEYSEPARATOR}{field}"
