from shared.util import is_reserved_field


def test_is_reserved_field_1():
    assert is_reserved_field("meta_something")


def test_is_reserved_field_2():
    assert is_reserved_field("meta")


def test_is_reserved_field_None():
    assert is_reserved_field(None) is False


def test_is_reserved_field_other_string():
    assert is_reserved_field("some_string") is False
