import enum
from datetime import date
from enum import Enum
from typing import Any, Dict, Optional

from nasty.util.time import yyyy_mm_dd_date


class Query:
    """Data class to store values that define a Twitter search query."""

    class Filter(Enum):
        TOP = enum.auto()
        LATEST = enum.auto()
        PHOTOS = enum.auto()
        VIDEOS = enum.auto()

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
        def from_json(cls, obj: str) -> 'Query.Filter':
            return cls[obj]

    def __init__(self,
                 query: str,
                 since: Optional[date] = None,
                 until: Optional[date] = None,
                 filter: Filter = Filter.TOP,
                 lang: str = 'en'):
        """Construct a new query.

        :param query: String that should be searched for. Twitter allows some
            advanced operations here, like exact phrase match, negative match,
            AND/OR, and to/from specific users. For more details, see:
            https://help.twitter.com/en/using-twitter/twitter-advanced-search

            There is no guarantee that the query string will be contained in the
            Tweet text. It could also be part of the name of the authoring user,
            or even the title of a linked external website.
        :param since: Only search Tweets written after this date (inclusive).
        :param until: Only search Tweets written before this date (exclusive).
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
        return (type(self) == type(other)) and (self.__dict__ == other.__dict__)

    def to_json(self) -> Dict:
        return {
            'query': self.query,
            'since': self.since.isoformat() if self.since else None,
            'until': self.until.isoformat() if self.until else None,
            'filter': self.filter.to_json(),
            'lang': self.lang,
        }

    @classmethod
    def from_json(cls, obj: Dict) -> 'Query':
        return cls(query=obj['query'],
                   since=(yyyy_mm_dd_date(obj['since'])
                          if obj['since'] else None),
                   until=(yyyy_mm_dd_date(obj['until'])
                          if obj['until'] else None),
                   filter=cls.Filter.from_json(obj['filter']),
                   lang=obj['lang'])
