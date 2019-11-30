from abc import ABC

from overrides import overrides
from typing_extensions import Final

from ..request.request import Request
from ..tweet.tweet import Tweet
from ..tweet.tweet_stream import TweetStream


class RetrieverTweetStream(TweetStream):
    @overrides
    def __init__(self, retriever: 'Retriever'):
        self._retriever: Final = retriever
        ...

    @overrides
    def __next__(self) -> Tweet:
        ...

    @property
    def retriever(self) -> 'Retriever':
        return self._retriever


class Retriever(ABC):
    _TWEET_STREAM_TYPE = RetrieverTweetStream

    def __init__(self, request: Request):
        self._request: Final = request
        self._tweet_stream: Final = self._TWEET_STREAM_TYPE(self)

    # Accessors to get variable of correct type:

    @property
    def request(self) -> Request:
        return self._request

    @property
    def tweet_stream(self) -> RetrieverTweetStream:
        return self._tweet_stream
