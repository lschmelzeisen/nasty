"""
Class collection containing the main Tweet class.
As well as a class for Hashtag, UserMention and TweetURLMapping
"""
import json
from typing import Dict, List, Tuple


class Hashtag:
    """The Hashtag class. Hashtag has it's text and the indices."""

    def __init__(self, text: str, indices: Tuple[int, int]):
        # e.g. "brexit"
        self.text = text
        # e.g. (16,22)
        self.indices = indices

    def __str__(self):
        return self.__dict__.__str__()


class UserMention:
    """The UserMention class. Got a @screen_name,
    if mentioned and not only answered too the user_id and the indices"""

    def __init__(self, screen_name: str, id_str: str, indices: Tuple[int, int]):
        # e.g. OHiwi-2
        self.screen_name = screen_name
        # e.g. "1117712996795658241"
        self.id_str = id_str
        # e.g. (14, 21)
        self.indices = indices

    def __str__(self):
        return self.__dict__.__str__()


class TweetURLMapping:
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

    def __str__(self):
        return self.__dict__.__str__()


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
                 urls: List[TweetURLMapping],
                 evaluation: List[str] = list()) -> None:
        tweet_id = str(tweet_id)
        self.created_at = created_at
        self.id_str = tweet_id
        self.full_text = full_text
        self.hashtags = hashtags
        self.user_mentions = user_mentions
        self.urls = urls
        self.name = name
        self.screen_name = screen_name
        self.evaluation = evaluation

    def __repr__(self):
        return type(self).__name__ + self.to_json()

    def to_json(self) -> str:
        """Return a json serializable dict of this tweet"""

        def to_dict_list(entities: List) -> List[Dict]:
            """Collects every entity of one type and form a list of dicts.
            Manly for toString cases."""
            temp = []
            for entity in entities:
                temp.append(entity.__dict__)
            return temp

        user = {"name": self.name, "screen_name": self.screen_name}
        entities = {"hashtags": to_dict_list(self.hashtags),
                    "user_mentions": to_dict_list(self.user_mentions),
                    "urls": to_dict_list(self.urls)}
        json_dict = dict()
        json_dict["created_at"] = self.created_at
        json_dict["id_str"] = self.id_str
        json_dict["full_text"] = self.full_text
        json_dict["entities"] = entities
        json_dict["user"] = user
        if self.evaluation:
            json_dict["evaluation"] = self.evaluation
        return json.dumps(json_dict)
