from typing import cast

from overrides import overrides

from .._util.typing_ import checked_cast
from ..tweet.conversation_tweet_stream import ConversationTweetStream
from .retriever import Retriever, RetrieverTweetStream


class ConversationRetrieverTweetStream(RetrieverTweetStream, ConversationTweetStream):
    @property  # type: ignore  # see https://github.com/python/mypy/issues/1362y
    @overrides
    def retriever(self) -> "ConversationRetriever":
        return checked_cast(ConversationRetriever, self._retriever)


class ConversationRetriever(Retriever):
    _TWEET_STREAM_TYPE = ConversationRetrieverTweetStream

    @property  # type: ignore  # see https://github.com/python/mypy/issues/1362
    @overrides
    def tweet_stream(self) -> "ConversationRetrieverTweetStream":
        return cast(ConversationRetrieverTweetStream, self._tweet_stream)
