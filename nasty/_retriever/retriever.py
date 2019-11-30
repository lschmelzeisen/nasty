#
# Copyright 2019 Lukas Schmelzeisen
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

from overrides import overrides
from typing_extensions import Final

from ..request.request import Request
from ..tweet.tweet import Tweet
from ..tweet.tweet_stream import TweetStream


class RetrieverTweetStream(TweetStream):
    @overrides
    def __init__(self, retriever: "Retriever"):
        self._retriever: Final = retriever

    @overrides
    def __next__(self) -> Tweet:
        pass

    @property
    def retriever(self) -> "Retriever":
        return self._retriever


class Retriever(ABC):
    _TWEET_STREAM_TYPE = RetrieverTweetStream

    def __init__(self, request: Request):
        self._request: Final = request
        self._tweet_stream: Final = self._TWEET_STREAM_TYPE(self)

    # Accessors to get variable of correct type:

    @property
    def request(self) -> Request:
        return self._request

    @property
    def tweet_stream(self) -> RetrieverTweetStream:
        return self._tweet_stream
