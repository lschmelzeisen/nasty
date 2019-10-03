import enum
from datetime import date
from enum import Enum
from logging import getLogger
from typing import Any, Dict, Optional

from nasty.init import init_nasty
from nasty.timeline import Timeline
from nasty.util.time import yyyy_mm_dd_date


class Search(Timeline):
    """Searches Tweets matching a query.

    The Tweets contained in the result and their sorting is determined by
    Twitter and will likely change when running with the same inputs
    multiple times. Also in some cases, Twitter stops sending results
    early, even though more matching Tweets would exists. However, there is
    no way to detect this.
    """

    class Query:
        """Data class to store values that define a Twitter search query."""

        class Filter(Enum):
            TOP = enum.auto()
            LATEST = enum.auto()
            PHOTOS = enum.auto()
            VIDEOS = enum.auto()

            DEFAULT_FILTER = TOP

            @property
            def url_param(self) -> Optional[str]:
                return {
                    self.LATEST: 'live',
                    self.PHOTOS: 'image',
                    self.VIDEOS: 'video',
                }.get(self, None)

            @property
            def result_filter(self) -> Optional[str]:
                return {
                    self.PHOTOS: 'image',
                    self.VIDEOS: 'video',
                }.get(self, None)

            @property
            def tweet_search_mode(self) -> Optional[str]:
                return {
                    self.LATEST: 'live',
                }.get(self, None)

            def to_json(self) -> str:
                return self.name

            @classmethod
            def from_json(cls, obj: str) -> 'Search.Query.Filter':
                return cls[obj]

        def __init__(self,
                     query: str,
                     since: Optional[date] = None,
                     until: Optional[date] = None,
                     filter: Filter = Filter.DEFAULT_FILTER,
                     lang: str = 'en'):
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
            :param filter: Method to sort/filter Tweets.
            :param lang: Only search Tweets written in this language.
            """

            self.query = query
            self.since = since
            self.until = until
            self.filter = filter
            self.lang = lang

        @property
        def url_param(self) -> str:
            """Transforms the stored query into the form that can be submitted to
            Twitter as an URL param.

            Does not perform URL escaping.
            """

            result = self.query

            if self.since:
                result += ' since:{}'.format(self.since.isoformat())
            if self.until:
                result += ' until:{}'.format(self.until.isoformat())

            result += ' lang:{}'.format(self.lang)

            return result

        def __repr__(self) -> str:
            return type(self).__name__ + repr(self.to_json())

        def __eq__(self, other: Any) -> bool:
            return (type(self) == type(other)) and (
                    self.__dict__ == other.__dict__)

        def to_json(self) -> Dict[str, Any]:
            obj = {}
            obj['query'] = self.query

            if self.since:
                obj['since'] = self.since.isoformat()
            if self.until:
                obj['until'] = self.until.isoformat()

            if self.filter != self.Filter.DEFAULT_FILTER:
                obj['filter'] = self.filter.to_json()

            obj['lang'] = self.lang

            return obj

        @classmethod
        def from_json(cls, obj: Dict[str, Any]) -> 'Search.Query':
            return cls(query=obj['query'],
                       since=(yyyy_mm_dd_date(obj['since'])
                              if 'since' in obj else None),
                       until=(yyyy_mm_dd_date(obj['until'])
                              if 'until' in obj else None),
                       filter=(cls.Filter.from_json(obj['filter'])
                               if 'filter' in obj
                               else cls.Filter.DEFAULT_FILTER),
                       lang=obj['lang'])

    def __init__(self,
                 query: 'Query',
                 max_tweets: Optional[int] = 100,
                 batch_size: int = Timeline.DEFAULT_BATCH_SIZE):
        """"Constructs a new Search.

        :param query: The query to search for.
        :param max_tweets: Stop the search after this many tweets have been
            found. Set to None in order to receive as many Tweets as possible.
            Note that this can return quite a lot of tweets, especially if using
            Filter.LATEST and no date range.
        :param batch_size: The batch size in which Tweets should be queried.

            The normal web interface always queries 20 Tweets per batch. Twitter
            interprets this parameter more as a guideline and can either return
            more or less then the requested amount. This does not indicate that
            no more matching Tweets exist after this batch.

            Note that by setting anything unequal to 20 here, we make ourselves
            easily distinguishable from normal web browser. Additionally,
            advanced queries like using AND or OR seem to no longer work as
            intended.

            This parameter can be used to speed up the search performance, by
            reducing the HTTP overhead as less requests have to be performed per
            returned Tweet. If you want to do this, we identified 100 to be a
            good value because increasing it further does seem not return more
            Tweets per request.
        :return: Iterable of tweets that match the query.
        """

        super().__init__(max_tweets=max_tweets, batch_size=batch_size)
        self.query = query

        logger = getLogger(__name__)
        logger.debug('Searching tweets matching {}.'.format(self.query))

    def _timeline_url(self) -> Dict:
        return {
            'url': 'https://mobile.twitter.com/search',
            'params': {
                'lang': self.query.lang,
                'q': self.query.url_param,
                'src': 'typed_query',
                'f': self.query.filter.url_param,
            },
        }

    def _batch_url(self, cursor: Optional[str] = None) -> Dict:
        return {
            'url': 'https://api.twitter.com/2/search/adaptive.json',
            'params': {
                # Not sure what most of the parameters with fixed values do. We
                # set them so that they are identical to those sent from the
                # normal web interface.
                'include_profile_interstitial_type': '1',
                'include_blocking': '1',
                'include_blocked_by': '1',
                'include_followed_by': '1',
                'include_want_retweets': '1',
                'include_mute_edge': '1',
                'include_can_dm': '1',
                'include_can_media_tag': '1',
                'skip_status': '1',
                'cards_platform': 'Web-12',
                'include_cards': '1',
                'include_composer_source': 'true',
                'include_ext_alt_text': 'true',
                'include_reply_count': '1',
                'tweet_mode': 'extended',
                'include_entities': 'true',
                'include_user_entities': 'true',
                'include_ext_media_color': 'true',
                'include_ext_media_availability': 'true',
                'send_error_codes': 'true',
                'q': self.query.url_param,
                'count': self.batch_size,
                'result_filter': self.query.filter.result_filter,
                'tweet_search_mode': self.query.filter.tweet_search_mode,
                'query_source': 'typed_query',
                'cursor': cursor,
                'pc': '1',
                'spelling_corrections': '1',
                'ext': 'mediaStats,highlightedLabel,cameraMoment',
            },
        }


if __name__ == '__main__':
    init_nasty()
    logger = getLogger(__name__)

    query = Search.Query('trump',
                         since=date(2019, 6, 23), until=date(2019, 6, 24))
    for tweet in Search(query, max_tweets=1000):
        logger.info(tweet)
