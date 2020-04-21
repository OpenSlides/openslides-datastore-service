from typing import get_type_hints, NewType, get_origin, get_args, Any, Type, Union
from .exceptions import InvalidFormat
from .key_types import (assert_is_collection, assert_is_field, assert_is_fqid, assert_is_id)
from dataclasses import dataclass


Collection = NewType("Collection", str)
Field = NewType("Field", str)
Id = NewType("Id", int)
Fqid = NewType("Fqid", str)
Position = NewType("Position", int)


@dataclass
class SelfValidatingDataclass:
    def __post_init__(self):
        for key, type_hint in get_type_hints(self).items():
            value = getattr(self, key)
            if value is not None:
                origin = get_origin(type_hint)
                if origin == list:
                    inner_type = get_args(type_hint)[0]
                    for el in value:
                        self.validate(el, inner_type)
                elif origin == Union:
                    nested_types = list(get_args(type_hint))
                    if len(nested_types) == 2 and type(None) in nested_types:
                        nested_types.remove(type(None))
                        self.validate(value, nested_types[0])
                else:
                    self.validate(value, type_hint)

    def validate(self, value: Any, type: Type) -> None:
        if type == Collection:
            assert_is_collection(value)
        elif type == Field:
            assert_is_field(value)
        elif type == Id:
            assert_is_id(str(value))
        elif type == Fqid:
            assert_is_fqid(value)
        elif type == Position:
            if value <= 0:
                raise InvalidFormat("The position has to be >0")
