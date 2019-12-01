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

from typing import Iterable, Mapping, Optional, Type

from overrides import overrides

from nasty.tweet.tweet import TweetId

from ..request.replies import Replies
from .conversation_retriever import ConversationRetriever
from .retriever import RetrieverBatch


class RepliesRetrieverBatch(RetrieverBatch):
    @overrides
    def _tweet_ids(self) -> Iterable[TweetId]:
        pass

    @overrides
    def _next_cursor(self) -> Optional[str]:
        pass


class RepliesRetriever(ConversationRetriever[Replies, RepliesRetrieverBatch]):
    @classmethod
    @overrides
    def _retriever_batch_type(cls) -> Type[RepliesRetrieverBatch]:
        return RepliesRetrieverBatch

    @overrides
    def _timeline_url(self) -> Mapping[str, object]:
        pass

    @overrides
    def _batch_url(self) -> Mapping[str, object]:
        pass
