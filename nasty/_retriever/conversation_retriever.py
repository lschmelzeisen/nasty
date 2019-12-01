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
from typing import Type, TypeVar, cast

from overrides import overrides

from ..request.request import Request
from ..tweet.conversation_tweet_stream import ConversationTweetStream
from .retriever import Retriever, RetrieverBatch, RetrieverTweetStream


class ConversationRetrieverTweetStream(RetrieverTweetStream, ConversationTweetStream):
    pass


_T_Request = TypeVar("_T_Request", bound=Request)
_T_RetrieverBatch = TypeVar("_T_RetrieverBatch", bound=RetrieverBatch)


class ConversationRetriever(Retriever[_T_Request, _T_RetrieverBatch], ABC):
    @classmethod
    @overrides
    def _tweet_stream_type(cls) -> Type[ConversationRetrieverTweetStream]:
        return ConversationRetrieverTweetStream

    @property  # type: ignore  # see https://github.com/python/mypy/issues/1362
    @overrides
    def tweet_stream(self) -> "ConversationRetrieverTweetStream":
        return cast(ConversationRetrieverTweetStream, self._tweet_stream)
