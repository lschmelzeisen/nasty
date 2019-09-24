from itertools import zip_longest
from typing import Iterable, List, TypeVar

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
