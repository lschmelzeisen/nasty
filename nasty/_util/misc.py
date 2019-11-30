from itertools import zip_longest
from typing import Iterable, Optional, Sequence, TypeVar

_T_item = TypeVar("_T_item")


def chunked(
    chunk_size: int,
    iterable: Iterable[_T_item],
    pad: bool = False,
    pad_value: Optional[_T_item] = None,
) -> Iterable[Sequence[_T_item]]:
    """Separate an iterable into equal size chunks."""

    iters = [iter(iterable)] * chunk_size
    for chunk in zip_longest(*iters, fillvalue=pad_value):
        if pad:
            yield list(chunk)
        else:
            yield [item for item in chunk if item is not None]
