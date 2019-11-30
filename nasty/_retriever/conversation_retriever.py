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

from typing import cast

from overrides import overrides

from .._util.typing_ import checked_cast
from ..tweet.conversation_tweet_stream import ConversationTweetStream
from .retriever import Retriever, RetrieverTweetStream


class ConversationRetrieverTweetStream(RetrieverTweetStream, ConversationTweetStream):
    @property  # type: ignore  # see https://github.com/python/mypy/issues/1362y
    @overrides
    def retriever(self) -> "ConversationRetriever":
        return checked_cast(ConversationRetriever, self._retriever)


class ConversationRetriever(Retriever):
    _TWEET_STREAM_TYPE = ConversationRetrieverTweetStream

    @property  # type: ignore  # see https://github.com/python/mypy/issues/1362
    @overrides
    def tweet_stream(self) -> "ConversationRetrieverTweetStream":
        return cast(ConversationRetrieverTweetStream, self._tweet_stream)
