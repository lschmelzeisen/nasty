from abc import ABC, abstractmethod
from typing import Iterable, Iterator

from overrides import overrides

from .tweet import Tweet


class TweetStream(ABC, Iterator[Tweet], Iterable[Tweet]):
    @overrides
    def __iter__(self) -> Iterator[Tweet]:
        return self

    @abstractmethod
    @overrides
    def __next__(self) -> Tweet:
        raise NotImplementedError()
