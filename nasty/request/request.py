from abc import ABC, abstractmethod
from typing import Dict, Mapping, Optional

from overrides import overrides
from typing_extensions import Final, final

from .._util.json_ import JsonSerializable
from ..tweet.tweet_stream import TweetStream

DEFAULT_MAX_TWEETS: Final = 100
DEFAULT_BATCH_SIZE: Final = 20


class Request(ABC, JsonSerializable):
    def __init__(self, *, max_tweets: Optional[int], batch_size: int):
        self.max_tweets: Final = max_tweets
        self.batch_size: Final = batch_size

    @final
    @overrides
    def __repr__(self) -> str:
        return type(self).__name__ + repr(self.to_json())

    @final
    @overrides
    def __eq__(self, other: object) -> bool:
        return type(self) == type(other) and self.__dict__ == other.__dict__

    @abstractmethod
    @overrides
    def to_json(self) -> Mapping[str, object]:
        obj: Dict[str, object] = {
            "type": type(self).__name__,
        }
        if self.max_tweets != DEFAULT_MAX_TWEETS:
            obj["max_tweets"] = self.max_tweets
        if self.batch_size != DEFAULT_BATCH_SIZE:
            obj["batch_size"] = self.batch_size
        return obj

    @classmethod
    @abstractmethod
    @overrides
    def from_json(cls, obj: Mapping[str, object]) -> "Request":
        from nasty.request.search import Search
        from nasty.request.replies import Replies
        from nasty.request.thread import Thread

        if obj["type"] == Search.__name__:
            return Search.from_json(obj)
        elif obj["type"] == Replies.__name__:
            return Replies.from_json(obj)
        elif obj["type"] == Thread.__name__:
            return Thread.from_json(obj)

        raise RuntimeError("Unknown request type: '{}'.".format(obj["type"]))

    @abstractmethod
    def request(self) -> TweetStream:
        raise NotImplementedError()
