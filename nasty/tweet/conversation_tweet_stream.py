from abc import abstractmethod

from overrides import overrides

from .tweet import Tweet
from .tweet_stream import TweetStream


class ConversationTweetStream(TweetStream):
    # Repeating abstractmethod definitions of base class to not trigger
    # PyCharm's inspection to implement abstract base methods.

    @abstractmethod
    @overrides
    def __next__(self) -> Tweet:
        raise NotImplementedError()
