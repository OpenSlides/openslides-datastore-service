from dataclasses import dataclass
from textwrap import dedent
from typing import Any, Optional, Type, Union, get_args, get_origin, get_type_hints

from datastore.shared.typing import (
    Collection,
    Field,
    Fqfield,
    Fqid,
    Id,
    Position,
    custom_types,
)

from .exceptions import BadCodingError, InvalidFormat
from .key_types import (
    assert_is_collection,
    assert_is_field,
    assert_is_fqfield,
    assert_is_fqid,
    assert_is_id,
)


@dataclass
class SelfValidatingDataclass:
    """
    A self-validating dataclass. Reads the type hints from the subclass and validates
    the values accordingly. Supports collection, field, fqid, id and position,
    Optional[<supported_type>] and List[<supported_type>].
    """

    def __post_init__(self):
        # mypy wants get_type_hints to be called with a callable...
        for key, type_hint in get_type_hints(self).items():  # type: ignore
            value = getattr(self, key)
            if value is not None:
                self.validate_nested_types(type_hint, value)

    def validate_nested_types(self, type_hint: Type, value: Any) -> None:
        origin = get_origin(type_hint)
        type_hint = self.normalize_type_hint(type_hint)
        if origin == Union:
            if type_hint in custom_types:
                self.validate(value, type_hint)
            else:
                nested_types = get_args(type_hint)
                errors = []
                for nested_type in nested_types:
                    try:
                        self.validate_nested_types(nested_type, value)
                        break
                    except AssertionError:
                        pass
                    except InvalidFormat as e:
                        errors.append(e)
                else:
                    if not len(errors):
                        raise BadCodingError(
                            dedent(
                                """
                            Given type does not match the type annotation.
                            Value: %s
                            Type hint: %s"
                            """
                            )
                            % (value, type_hint)
                        )
                    elif len(errors) == 1:
                        raise errors[0]
                    else:
                        raise InvalidFormat(
                            "The following errors occurred when trying to validate the\
                                data: %s"
                            % errors
                        )
        elif origin == list:
            nested_type = get_args(type_hint)[0]
            if not get_origin(nested_type):
                assert all(isinstance(el, nested_type) for el in value)
            for el in value:
                self.validate(el, nested_type)

    def normalize_type_hint(self, type_hint: Type) -> Type:
        for t in custom_types:
            if Optional[t] == type_hint:
                return t  # type: ignore
        return type_hint

    def validate(self, value: Any, type: Type) -> None:
        # TODO: remove type comments as soon as mypy is fixed
        # (which may be a while, see https://github.com/python/mypy/issues/5354)
        if type == Collection:  # type: ignore
            assert_is_collection(value)
        elif type == Field:  # type: ignore
            assert_is_field(value)
        elif type == Id:  # type: ignore
            assert_is_id(str(value))
        elif type == Fqid:  # type: ignore
            assert_is_fqid(value)
        elif type == Fqfield:  # type: ignore
            assert_is_fqfield(value)
        elif type == Position:  # type: ignore
            if value <= 0:
                raise InvalidFormat("The position has to be >0")
