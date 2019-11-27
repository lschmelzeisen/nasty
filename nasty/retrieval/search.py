import enum
import logging
from datetime import date
from enum import Enum
from logging import getLogger
from typing import Any, Dict, Iterable, Optional

from nasty.jobs import Job
from nasty.retrieval.timeline import Timeline
from nasty.util.logging import setup_logging
from nasty.util.time import yyyy_mm_dd_date


class Search(Timeline):
    """Searches Tweets matching a query.

    The Tweets contained in the result and their sorting is determined by
    Twitter and will likely change when running with the same inputs
    multiple times. Also in some cases, Twitter stops sending results
    early, even though more matching Tweets would exists. However, there is
    no way to detect this.
    """

    class Work(Timeline.Work):
        def __init__(self,
                     query: 'Search.Query',
                     max_tweets: Optional[int],
                     batch_size: Optional[int]):
            super().__init__('search', max_tweets, batch_size)
            self.query = query

        def to_timeline(self) -> Timeline:
            return Search(self.query, self.max_tweets, self.batch_size)

        def to_json(self) -> Dict[str, Any]:
            obj = {
                'type': self.type,
                'query': self.query.to_json(),
            }

            if self.max_tweets is not None:
                obj['max_tweets'] = self.max_tweets
            if self.batch_size is not None:
                obj['batch_size'] = self.batch_size

            return obj

        @classmethod
        def from_json(cls, obj: Dict[str, Any]) -> Timeline.Work:
            assert obj['type'] == 'search'
            return cls(Search.Query.from_json(obj['query']),
                       obj.get('max_tweets'),
                       obj.get('batch_size'))

    class Query:
        """Data class to store values that define a Twitter search query."""

        class Filter(Enum):
            """Different sorting/filtering rules for Twitter search results.

            - TOP: Sort result Tweets by popularity (e.g., when a lot of people
              are interacting with or sharing via Retweets and replies)
            - LATEST: Sort result Tweets by most-recent post date.
            - PHOTOS: To only see Tweets that includes photos.
            - PHOTOS: To only see Tweets that includes videos.

            See:
            https://help.twitter.com/en/using-twitter/top-search-results-faqs
            """

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
            obj = {'query': self.query}

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
                 batch_size: Optional[int] = None):
        """"Constructs a new search view.

        See the base class for documentation of the max_tweets and batch_size
        parameters.

        :param query: The query to search for.
        """

        super().__init__(max_tweets=max_tweets, batch_size=batch_size)
        self.query = query

        logger = getLogger(__name__)
        logger.debug('Searching tweets matching {}.'.format(self.query))

    def to_job(self) -> Job:
        return Job(self.Work(self.query, self.max_tweets, self.batch_size))

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

    def _tweet_ids_in_batch(self, batch: Dict) -> Iterable[str]:
        # Search results are contained in instructions. The first batch of a
        # search will look like this:
        # { ...
        #   "timeline": {
        #     "id": "search-6602913952152093875",
        #     "instructions": [
        #       { "addEntries": {
        #           "entries": [
        #             { "entryId": "sq-I-t-1155486497451184128", ... },
        #             { "entryId": "sq-I-t-1194473608061607936", ... },
        #             { "entryId": "sq-M-1-d7721393", ... },
        #             { "entryId": "sq-E-1981039365", ... },
        #             ...
        #             { "entryId": "sq-cursor-top", ... },
        #             { "entryId": "sq-cursor-bottom", ... }]}}],
        #     ... }}
        #
        # We need to separate the following entity types:
        # - "sq-I-t-..." are the Tweets matching the search query.
        # - "sq-M-..." contain supplementary information like user profiles that
        #   are somehow related to the matching Tweets (usually occurs once).
        # - "sq-E-..." seem to contain suggested live events (occur rarely).
        # - "sq-cursor-..." entries contain the cursors to fetch the next batch.
        #
        # All following batches will look similar except that the
        # "sq-cursor-..." entries are now differently placed:
        # { ...
        #   "timeline": {
        #     "id": "search-6602913956034868792",
        #     "instructions": [
        #       { "addEntries": {
        #           "entries": [
        #             { "entryId": "sq-I-t-1157704001112219650", ... },
        #             { "entryId": "sq-I-t-1156734175040266240", ... },
        #             { ... }]}},
        #       { "replaceEntry": {
        #           "entryIdToReplace": "sq-cursor-top",
        #           "entry": {
        #             "entryId": "sq-cursor-top", ... }}},
        #       { "replaceEntry": {
        #           "entryIdToReplace": "sq-cursor-bottom",
        #           "entry": {
        #             "entryId": "sq-cursor-bottom", ... }}}],
        #     ... }}
        instructions = batch['timeline']['instructions']

        for entry in instructions[0]['addEntries']['entries']:
            if entry['entryId'].startswith('sq-I-t-'):
                # Matching Tweet entries look like this:
                # { "entryId": "sq-I-t-1155486497451184128",
                #   "sortIndex": "999970",
                #   "content": {
                #     "item": {
                #       "content": {
                #         "tweet": {
                #           "id": "1155486497451184128",
                #           "displayType": "Tweet",
                #           "highlights": { ... }}}
                #       ... }}}
                yield entry['content']['item']['content']['tweet']['id']
            elif entry['entryId'].startswith('sq-M-'):
                pass
            elif entry['entryId'].startswith('sq-E-'):
                pass
            elif entry['entryId'].startswith('sq-cursor-'):
                pass
            else:
                raise RuntimeError('Unknown entry type in entry-ID: {}'
                                   .format(entry['entryId']))

    def _next_cursor_from_batch(self, batch: Dict) -> Optional[str]:
        # As documented in _tweet_ids_in_batch(), the cursor objects can occur
        # either as part of "addEntries" or replaceEntry". We are only
        # interested in sq-cursor-bottom and I'm not sure what sq-cursor-top is
        # for. The actual cursor entry will look like this:
        # { "entryId": "sq-cursor-bottom",
        #   "sortIndex": "0",
        #   "content": {
        #     "operation": {
        #       "cursor": {
        #         "value": "scroll:thGAVUV...",
        #         "cursorType": "Bottom" }}}}
        instructions = batch['timeline']['instructions']
        cursor_entry = instructions[0]['addEntries']['entries'][-1]
        if cursor_entry['entryId'] != 'sq-cursor-bottom':
            cursor_entry = instructions[-1]['replaceEntry']['entry']
        if cursor_entry['entryId'] != 'sq-cursor-bottom':
            raise RuntimeError('Could not locate cursor entry.')
        return cursor_entry['content']['operation']['cursor']['value']


if __name__ == '__main__':
    setup_logging(logging.DEBUG)
    logger = getLogger(__name__)

    query = Search.Query(
        'trump', since=date(2019, 6, 23), until=date(2019, 6, 24))
    for tweet in Search(query, max_tweets=1000):
        logger.info(tweet)
