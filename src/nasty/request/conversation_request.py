#
# Copyright 2019-2020 Lukas Schmelzeisen
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
from abc import ABC
from typing import Dict, Mapping, Optional, Type, TypeVar, cast

from overrides import overrides
from typing_extensions import Final

from .._util.typing_ import checked_cast
from ..tweet.tweet import TweetId
from .request import DEFAULT_BATCH_SIZE, DEFAULT_MAX_TWEETS, Request

_T_ConversationRequest = TypeVar("_T_ConversationRequest", bound="ConversationRequest")


class ConversationRequest(Request, ABC):
    def __init__(
        self,
        tweet_id: TweetId,
        *,
        max_tweets: Optional[int] = DEFAULT_MAX_TWEETS,
        batch_size: int = DEFAULT_BATCH_SIZE,
    ):
        super().__init__(max_tweets=max_tweets, batch_size=batch_size)
        self.tweet_id: Final = tweet_id

    @overrides
    def to_json(self) -> Mapping[str, object]:
        obj: Dict[str, object] = {
            "type": None,  # Will be set in super(), but forces order.
            "tweet_id": self.tweet_id,
        }
        obj.update(super().to_json())
        return obj

    @classmethod
    @overrides
    def from_json(
        cls: Type[_T_ConversationRequest], obj: Mapping[str, object]
    ) -> _T_ConversationRequest:
        assert obj["type"] == cls.__name__
        return cls(
            tweet_id=checked_cast(TweetId, obj["tweet_id"]),
            max_tweets=(
                cast(Optional[int], obj["max_tweets"])
                if "max_tweets" in obj
                else DEFAULT_MAX_TWEETS
            ),
            batch_size=(
                checked_cast(int, obj["batch_size"])
                if "batch_size" in obj
                else DEFAULT_BATCH_SIZE
            ),
        )
