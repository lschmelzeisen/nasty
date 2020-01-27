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
from typing import Dict, Mapping, Optional

from overrides import overrides
from typing_extensions import Final, final

from .._util.json_ import JsonSerializable
from ..tweet.tweet_stream import TweetStream

DEFAULT_MAX_TWEETS: Final = 100
DEFAULT_BATCH_SIZE: Final = 20


class Request(ABC, JsonSerializable):
    def __init__(self, *, max_tweets: Optional[int], batch_size: int):
        """Construct a new timeline view.

         :param max_tweets: Stop retrieving Tweets after this many tweets have
             been found. Set to None in order to receive as many Tweets as
             possible. Note that this can return quite a lot of tweets,
             especially if using Search, Filter.LATEST and no date range.
         :param batch_size: The batch size in which Tweets should be retrieved.

             The normal web interface always queries 20 Tweets per batch. Twitter
             interprets this parameter more as a guideline and can either return
             more or less then the requested amount. This does not indicate that
             no more matching Tweets exist after this batch.

             Note that by setting anything unequal to 20 here, we make ourselves
             easily distinguishable from a normal web browser. Additionally,
             advanced queries like using AND or OR seem to no longer work as
             intended. For Thread and Reply, increasing the batch_size is likely
             to also increase the number of results (no idea why Twitter is doing
             this).

             This parameter can be used to speed up the retrieval performance, by
             reducing the HTTP overhead as less requests have to be performed per
             returned Tweet. If you want to do this, we identified 100 to be a
             good value because increasing it further does seem not return more
             Tweets per request.
         """

        if max_tweets is not None and max_tweets <= 0:
            raise ValueError("If max_tweets is given, it must be positive.")
        if batch_size <= 0:
            raise ValueError("batch_size must be positive.")

        self.max_tweets: Final = max_tweets
        self.batch_size: Final = batch_size

    @final
    @overrides
    def __eq__(self, other: object) -> bool:
        return type(self) == type(other) and self.__dict__ == other.__dict__

    @abstractmethod
    @overrides
    def to_json(self) -> Mapping[str, object]:
        obj: Dict[str, object] = {
            "type": type(self).__name__,
        }
        if self.max_tweets != DEFAULT_MAX_TWEETS:
            obj["max_tweets"] = self.max_tweets
        if self.batch_size != DEFAULT_BATCH_SIZE:
            obj["batch_size"] = self.batch_size
        return obj

    @classmethod
    @abstractmethod
    @overrides
    def from_json(cls, obj: Mapping[str, object]) -> "Request":
        from .search import Search
        from .replies import Replies
        from .thread import Thread

        if obj["type"] == Search.__name__:
            return Search.from_json(obj)
        elif obj["type"] == Replies.__name__:
            return Replies.from_json(obj)
        elif obj["type"] == Thread.__name__:
            return Thread.from_json(obj)

        raise RuntimeError("Unknown request type: '{}'.".format(obj["type"]))

    @abstractmethod
    def request(self) -> TweetStream:
        raise NotImplementedError()
