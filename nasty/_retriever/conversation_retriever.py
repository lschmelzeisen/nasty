from overrides import overrides
from typing import cast

from .retriever import Retriever, RetrieverTweetStream
from .._util.typing_ import checked_cast
from ..tweet.conversation_tweet_stream import ConversationTweetStream


class ConversationRetrieverTweetStream(RetrieverTweetStream,
                                       ConversationTweetStream):
    @property
    def retriever(self) -> 'ConversationRetriever':
        return checked_cast(ConversationRetriever, self._retriever)

    ...


class ConversationRetriever(Retriever):
    _TWEET_STREAM_TYPE = ConversationRetrieverTweetStream

    @property  # type: ignore  # see https://github.com/python/mypy/issues/1362
    @overrides
    def tweet_stream(self) -> 'ConversationRetrieverTweetStream':
        return cast(ConversationRetrieverTweetStream, self._tweet_stream)
