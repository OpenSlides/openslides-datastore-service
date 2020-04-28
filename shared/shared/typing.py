from typing import Any, Dict, List, NewType, Union


JSON = Union[str, int, float, bool, None, Dict[str, Any], List[Any]]


Model = Dict[str, Any]

_Collection = NewType("_Collection", str)
_Field = NewType("_Field", str)
_Id = NewType("_Id", int)
_Fqid = NewType("_Fqid", str)
_Position = NewType("_Position", int)

Collection = Union[str, _Collection]
Field = Union[str, _Field]
Id = Union[int, _Id]
Fqid = Union[str, _Fqid]
Position = Union[int, _Position]

# TODO: remove type comments as soon as mypy is fixed
# (which may be a while, see https://github.com/python/mypy/issues/5354)
custom_types = [Collection, Field, Id, Fqid, Position]  # type: ignore
