from datetime import datetime

from overrides import overrides
from typing import Mapping, cast
from typing_extensions import Final

from .._util.consts import TWITTER_CREATED_AT_FORMAT
from .._util.json_ import JsonSerializable
from .._util.typing_ import checked_cast

TweetId = str


class Tweet(JsonSerializable):
    """Data class to wrap Tweet JSON objects."""

    def __init__(self, json: Mapping[str, object]):
        self.json: Final = json

    @overrides
    def __repr__(self) -> str:
        return type(self).__name__ + repr({
            'created_at': self.created_at,
            'id': self.id,
            'text': self.text,
            'user': self.user,
            'url': self.url,
        })

    @overrides
    def __eq__(self, other: object) -> bool:
        return type(self) == type(other) and self.__dict__ == other.__dict__

    @property
    def created_at(self) -> datetime:
        return datetime.strptime(checked_cast(str, self.json['created_at']),
                                 TWITTER_CREATED_AT_FORMAT)

    @property
    def id(self) -> TweetId:
        return checked_cast(TweetId, self.json['id_str'])

    @property
    def text(self) -> str:
        return checked_cast(str, self.json['full_text'])

    @property
    def user(self) -> 'User':
        return User(cast(Mapping[str, object], self.json['user']))

    @property
    def url(self) -> str:
        return '{}/status/{}'.format(self.user.url, self.id)

    @overrides
    def to_json(self) -> Mapping[str, object]:
        return self.json

    @classmethod
    @overrides
    def from_json(cls, obj: Mapping[str, object]) -> 'Tweet':
        return cls(obj)


UserId = str


class User(JsonSerializable):
    """Data class to wrap Twitter user JSON objects."""

    def __init__(self, json: Mapping[str, object]):
        self.json: Final = json

    @overrides
    def __repr__(self) -> str:
        return type(self).__name__ + repr({
            'id': self.id,
            'name': self.name,
            'screen_name': self.screen_name,
            'url': self.url,
        })

    @overrides
    def __eq__(self, other: object) -> bool:
        return type(self) == type(other) and self.__dict__ == other.__dict__

    @property
    def id(self) -> UserId:
        return checked_cast(UserId, self.json['id_str'])

    @property
    def name(self) -> str:
        return checked_cast(str, self.json['name'])

    @property
    def screen_name(self) -> str:
        return checked_cast(str, self.json['screen_name'])

    @property
    def url(self) -> str:
        return 'https://twitter.com/{}'.format(self.screen_name)

    @overrides
    def to_json(self) -> Mapping[str, object]:
        return self.json

    @classmethod
    @overrides
    def from_json(cls, obj: Mapping[str, object]) -> 'User':
        return cls(obj)
