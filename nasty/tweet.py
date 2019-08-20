"""
Class collection containing the main Tweet class.
As well as a class for Hashtag, UserMention and TweetURLMapping
"""
from typing import Dict, List, Optional, Tuple


class Hashtag:
    """The Hashtag class. Hashtag has it's text and the indices."""

    def __init__(self, text: str, indices: Tuple[int, int]):
        # e.g. "brexit"
        self.text = text
        # e.g. (16,22)
        self.indices = indices

    def __repr__(self):
        return type(self).__name__ + repr(self.to_json())

    def to_json(self) -> Dict:
        return {
            'text': self.text,
            'indices': self.indices,
        }

    @classmethod
    def from_json(cls, obj: Dict) -> 'Hashtag':
        return cls(text=obj['text'],
                   indices=tuple(obj['indices']))


class UserMention:
    """The UserMention class. Got a @screen_name,
    if mentioned and not only answered too the user_id and the indices"""

    def __init__(self, screen_name: str, id_: str, indices: Tuple[int, int]):
        # e.g. OHiwi-2
        self.screen_name = screen_name
        # e.g. "1117712996795658241"
        self.id = id_
        # e.g. (14, 21)
        self.indices = indices

    def __repr__(self):
        return type(self).__name__ + repr(self.to_json())

    def to_json(self) -> Dict:
        return {
            'screen_name': self.screen_name,
            'id': self.id,
            'indices': self.indices,
        }

    @classmethod
    def from_json(cls, obj: Dict) -> 'UserMention':
        return cls(screen_name=obj['screen_name'],
                   id_=obj['id'],
                   indices=tuple(obj['indices']))


class TweetUrlMapping:
    """The TweetURLMapping class. Got the short url, the url and the displayed
    url + indices"""

    def __init__(self,
                 url: str,
                 expanded_url: str,
                 display_url: str,
                 indices: Tuple[int, int]):
        # e.g. "https:\/\/t.co\/Dw84m8xRGw" | short t.co link
        self.url = url
        # e.g. "http:\/\/google.com" | the whole unchanged link
        self.expanded_url = expanded_url
        # e.g. "google.com" | the displayed part of the whole unchanged link
        self.display_url = display_url
        # e.g. (18,41)
        self.indices = indices

    def __repr__(self):
        return type(self).__name__ + repr(self.to_json())

    def to_json(self) -> Dict:
        return {
            'url': self.url,
            'expanded_url': self.expanded_url,
            'display_url': self.display_url,
            'indices': self.indices,
        }

    @classmethod
    def from_json(cls, obj: Dict) -> 'TweetUrlMapping':
        return cls(url=obj['url'],
                   expanded_url=obj['expanded_url'],
                   display_url=obj['display_url'],
                   indices=tuple(obj['indices']))


class Tweet:
    """
    The main Tweet class.
    Got all information we can currently get from extracting it out of html
    data. That is: creation date, id, the text, hashtags, user mentions, urls,
    the authors name and short name.
    """

    # adv: bool   <= declares if its from API or ADVsearch. Want that?

    def __init__(self,
                 created_at: str,
                 tweet_id: str,
                 full_text: str,
                 name: str,
                 screen_name: str,
                 hashtags: List[Hashtag],
                 user_mentions: List[UserMention],
                 urls: List[TweetUrlMapping],
                 evaluation: Optional[List[str]] = None) -> None:
        self.created_at = created_at
        self.id_str = tweet_id
        self.full_text = full_text
        self.hashtags = hashtags
        self.user_mentions = user_mentions
        self.urls = urls
        self.name = name
        self.screen_name = screen_name
        self.evaluation = evaluation or []

    def __repr__(self):
        return type(self).__name__ + repr(self.to_json())

    def to_json(self) -> Dict:
        result = {
            'created_at': self.created_at,
            'id_str': self.id_str,
            'full_text': self.full_text,
            'entities': {
                'hashtags': [hashtag.to_json() for hashtag in self.hashtags],
                'user_mentions': [user_mention.to_json()
                                  for user_mention in self.user_mentions],
                'urls': [url.to_json() for url in self.urls]
            },
            'user': {
                'name': self.name,
                'screen_name': self.screen_name,
            }
        }

        if self.evaluation:
            result['evaluation'] = self.evaluation

        return result

    @classmethod
    def from_json(cls, obj: Dict) -> 'Tweet':
        return cls(created_at=obj['created_at'],
                   tweet_id=obj['id_str'],
                   full_text=obj['full_text'],
                   name=obj['user']['name'],
                   screen_name=obj['user']['screen_name'],
                   hashtags=[Hashtag.from_json(hashtag)
                             for hashtag in obj['entities']['hashtags']],
                   user_mentions=[UserMention.from_json(user_mention)
                                  for user_mention
                                  in obj['entities']['user_mentions']],
                   urls=[TweetUrlMapping.from_json(url)
                         for url in obj['entities']['urls']],
                   evaluation=obj.get('evaluation'))
