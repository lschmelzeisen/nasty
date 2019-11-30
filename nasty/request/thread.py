from overrides import overrides
from typing import Dict, Mapping, Optional, cast
from typing_extensions import Final

from .request import DEFAULT_BATCH_SIZE, DEFAULT_MAX_TWEETS, Request
from ..tweet.conversation_tweet_stream import ConversationTweetStream
from ..tweet.tweet import TweetId
from .._util.typing_ import checked_cast


class Thread(Request):
    def __init__(self,
                 tweet_id: TweetId,
                 *,
                 max_tweets: Optional[int] = DEFAULT_MAX_TWEETS,
                 batch_size: int = DEFAULT_BATCH_SIZE):
        super().__init__(max_tweets=max_tweets, batch_size=batch_size)
        self.tweet_id: Final = tweet_id

    @overrides
    def to_json(self) -> Mapping[str, object]:
        obj: Dict[str, object] = {
            'type': None,  # Will be set in super(), but forces order.
            'tweet_id': self.tweet_id,
        }
        obj.update(super().to_json())
        return obj

    @classmethod
    @overrides
    def from_json(cls, obj: Mapping[str, object]) -> 'Thread':
        assert obj['type'] == cls.__name__
        return cls(
            tweet_id=checked_cast(TweetId, obj['tweet_id']),
            max_tweets=(cast(Optional[int], obj['max_tweets'])
                        if 'max_tweets' in obj else DEFAULT_MAX_TWEETS),
            batch_size=(checked_cast(int, obj['batch_size'])
                        if 'batch_size' in obj else DEFAULT_BATCH_SIZE))

    @overrides
    def request(self) -> ConversationTweetStream:
        from nasty._retriever.thread_retriever import ThreadRetriever
        return ThreadRetriever(self).tweet_stream
