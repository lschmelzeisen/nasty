import enum
from datetime import date

from overrides import overrides
from typing import Dict, Mapping, Optional, cast
from typing_extensions import Final

from .request import DEFAULT_BATCH_SIZE, DEFAULT_MAX_TWEETS, Request
from ..tweet.tweet_stream import TweetStream
from .._util.json_ import JsonSerializableEnum
from .._util.time_ import yyyy_mm_dd_date
from .._util.typing_ import checked_cast


class SearchFilter(JsonSerializableEnum):
    """Different sorting/filtering rules for Twitter search results.

    - TOP: Sort result Tweets by popularity (e.g., when a lot of people
      are interacting with or sharing via Retweets and replies)
    - LATEST: Sort result Tweets by most-recent post date.
    - PHOTOS: To only see Tweets that includes photos.
    - PHOTOS: To only see Tweets that includes videos.

    See: https://help.twitter.com/en/using-twitter/top-search-results-faqs
    """

    TOP = enum.auto()
    LATEST = enum.auto()
    PHOTOS = enum.auto()
    VIDEOS = enum.auto()

    # @property
    # def url_param(self) -> Optional[str]:
    #     return {
    #         SearchFilter.LATEST: 'live',
    #         SearchFilter.PHOTOS: 'image',
    #         SearchFilter.VIDEOS: 'video',
    #     }.get(self, None)
    #
    # @property
    # def result_filter(self) -> Optional[str]:
    #     return {
    #         SearchFilter.PHOTOS: 'image',
    #         SearchFilter.VIDEOS: 'video',
    #     }.get(self, None)
    #
    # @property
    # def tweet_search_mode(self) -> Optional[str]:
    #     return {
    #         SearchFilter.LATEST: 'live',
    #     }.get(self, None)


DEFAULT_FILTER = SearchFilter.TOP


class Search(Request):
    def __init__(self,
                 query: str,
                 *,
                 since: Optional[date] = None,
                 until: Optional[date] = None,
                 filter_: SearchFilter = DEFAULT_FILTER,
                 lang: str = 'en',
                 max_tweets: Optional[int] = DEFAULT_MAX_TWEETS,
                 batch_size: int = DEFAULT_BATCH_SIZE):
        """Construct a new query.

        :param query: String that should be searched for. Twitter allows
            some advanced operations here, like exact phrase match, negative
            match, AND/OR, and to/from specific users. For more details,
            see:
            https://help.twitter.com/en/using-twitter/twitter-advanced-search

            There is no guarantee that the query string will be contained in
            the Tweet text. It could also be part of the name of the
            authoring user, or even the title of a linked external website.
        :param since: Only find Tweets written after this date (inclusive).
        :param until: Only find Tweets written before this date (exclusive).
        :param filter_: Method to sort/filter Tweets.
        :param lang: Only search Tweets written in this language.
        """

        super().__init__(max_tweets=max_tweets, batch_size=batch_size)
        self.query: Final = query
        self.since: Final = since
        self.until: Final = until
        self.filter: Final = filter_
        self.lang: Final = lang

    @overrides
    def to_json(self) -> Mapping[str, object]:
        obj: Dict[str, object] = {
            'type': None,  # Will be set in super(), but forces order.
            'query': self.query
        }
        if self.since:
            obj['since'] = self.since.isoformat()
        if self.until:
            obj['until'] = self.until.isoformat()
        obj['filter'] = self.filter.to_json()
        obj['lang'] = self.lang
        obj.update(super().to_json())
        return obj

    @classmethod
    @overrides
    def from_json(cls, obj: Mapping[str, object]) -> 'Search':
        assert obj['type'] == cls.__name__
        return cls(
            query=checked_cast(str, obj['query']),
            since=(yyyy_mm_dd_date(checked_cast(str, obj['since']))
                   if 'since' in obj else None),
            until=(yyyy_mm_dd_date(checked_cast(str, obj['until']))
                   if 'until' in obj else None),
            filter_=SearchFilter.from_json(
                cast(Mapping[str, object], obj['filter'])),
            lang=checked_cast(str, obj['lang']),
            max_tweets=(cast(Optional[int], obj['max_tweets'])
                        if 'max_tweets' in obj else DEFAULT_MAX_TWEETS),
            batch_size=(checked_cast(int, obj['batch_size'])
                        if 'batch_size' in obj else DEFAULT_BATCH_SIZE))

    @overrides
    def request(self) -> TweetStream:
        from .._retriever.search_retriever import SearchRetriever
        return SearchRetriever(self).tweet_stream

    # @property
    # def url_param(self) -> str:
    #     """Transforms the stored query into the form that can be submitted to
    #     Twitter as an URL param.
    #
    #     Does not perform URL escaping.
    #     """
    #
    #     result = self.query
    #
    #     if self.since:
    #         result += ' since:{}'.format(self.since.isoformat())
    #     if self.until:
    #         result += ' until:{}'.format(self.until.isoformat())
    #
    #     result += ' lang:{}'.format(self.lang)
    #
    #     return result
