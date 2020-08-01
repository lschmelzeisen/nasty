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

from abc import ABC, abstractmethod
from typing import Iterable, Mapping, Type, TypeVar, cast

from overrides import overrides

from ..request.conversation_request import ConversationRequest
from ..tweet.conversation_tweet_stream import ConversationTweetStream
from ..tweet.tweet import TweetId
from .retriever import Retriever, RetrieverBatch, RetrieverTweetStream


class ConversationRetrieverTweetStream(RetrieverTweetStream, ConversationTweetStream):
    # TODO: Access to tombstones count and meta-less Tweet-IDs
    pass


class ConversationRetrieverBatch(RetrieverBatch, ABC):
    def __init__(self, json: Mapping[str, Mapping[str, object]]):
        # TODO: See if this is necessary for ThreadRetriever
        self.num_tombstones = 0
        super().__init__(json)

    @abstractmethod
    @overrides
    def _tweet_ids(self) -> Iterable[TweetId]:
        pass


_T_ConversationRequest = TypeVar("_T_ConversationRequest", bound=ConversationRequest)


class ConversationRetriever(Retriever[_T_ConversationRequest], ABC):
    @classmethod
    @overrides
    def _tweet_stream_type(cls) -> Type[ConversationRetrieverTweetStream]:
        return ConversationRetrieverTweetStream

    @classmethod
    @overrides
    def _retriever_batch_type(cls) -> Type[ConversationRetrieverBatch]:
        return ConversationRetrieverBatch

    @property  # type: ignore  # see https://github.com/python/mypy/issues/1362
    @overrides
    def tweet_stream(self) -> "ConversationRetrieverTweetStream":
        return cast(ConversationRetrieverTweetStream, self._tweet_stream)

    @overrides
    def _timeline_url(self) -> Mapping[str, object]:
        return {"url": "https://mobile.twitter.com/_/status/" + self._request.tweet_id}

    @overrides
    def _batch_url(self) -> Mapping[str, object]:
        return {
            "url": (
                "https://api.twitter.com/2/timeline/conversation/{:s}.json".format(
                    self._request.tweet_id
                )
            ),
            "params": {
                "include_profile_interstitial_type": 1,
                "include_blocking": 1,
                "include_blocked_by": 1,
                "include_followed_by": 1,
                "include_want_retweets": 1,
                "include_mute_edge": 1,
                "include_can_dm": 1,
                "include_can_media_tag": 1,
                "skip_status": 1,
                "cards_platform": "Web-12",
                "include_cards": 1,
                "include_composer_source": "true",
                "include_ext_alt_text": "true",
                "include_reply_count": 1,
                "tweet_mode": "extended",
                "include_entities": "true",
                "include_user_entities": "true",
                "include_ext_media_color": "true",
                "include_ext_media_availability": "true",
                "send_error_codes": "true",
                "count": self._request.batch_size,
                "cursor": self._cursor,
                "ext": "mediaStats,highlightedLabel,cameraMoment",
            },
        }
