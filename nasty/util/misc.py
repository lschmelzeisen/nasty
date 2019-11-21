from itertools import zip_longest
from typing import Any, Iterable, List, Mapping, Sequence, TypeVar, Union

T = TypeVar('T')


def chunked(chunk_size: int,
            iterable: Iterable[T],
            pad: bool = False,
            pad_value: T = None) -> Iterable[List[T]]:
    """Separate an iterable into equal size chunks."""

    iters = [iter(iterable)] * chunk_size
    for chunk in zip_longest(*iters, fillvalue=pad_value):
        if pad:
            yield list(chunk)
        else:
            yield [item for item in chunk if item is not None]


def dict_deep_get(value: Union[Mapping, Sequence], *args) -> Any:
    for arg in args:
        if value is None:
            return None
        if isinstance(value, Mapping):
            value = value.get(arg, None)
        elif isinstance(value, Sequence):
            value = value[arg] if -len(value) <= arg < len(value) else None
        else:
            raise TypeError('(Nested) value must be either a Mapping or a'
                            'Sequence, was a {}.'.format(type(value)))
    return value
