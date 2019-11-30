from typing import Type, TypeVar

_T_type = TypeVar("_T_type")


def checked_cast(type_: Type[_T_type], value: object) -> _T_type:
    assert isinstance(value, type_)
    return value
