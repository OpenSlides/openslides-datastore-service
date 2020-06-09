from typing import Any, Dict, List, NewType, Union


JSON = Union[str, int, float, bool, None, Dict[str, Any], List[Any]]


Model = Dict[str, Any]

_Collection = NewType("_Collection", str)
_Field = NewType("_Field", str)
_Id = NewType("_Id", int)
_Fqid = NewType("_Fqid", str)
_Fqfield = NewType("_Fqfield", str)
_Position = NewType("_Position", int)

Collection = Union[str, _Collection]
Field = Union[str, _Field]
Id = Union[int, _Id]
Fqid = Union[str, _Fqid]
Fqfield = Union[str, _Fqfield]
Position = Union[int, _Position]

custom_types = [Collection, Field, Id, Fqid, Fqfield, Position]  # type: ignore
