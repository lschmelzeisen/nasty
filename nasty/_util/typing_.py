from typing import Type, TypeVar

T = TypeVar('T')


def checked_cast(type_: Type[T], value: object) -> T:
    assert isinstance(value, type_)
    return value
