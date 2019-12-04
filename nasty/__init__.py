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

from .cli.main import main
from .request.conversation_request import ConversationRequest
from .request.replies import Replies
from .request.request import DEFAULT_BATCH_SIZE, DEFAULT_MAX_TWEETS, Request
from .request.search import DEFAULT_FILTER, Search, SearchFilter
from .request.thread import Thread
from .request_executor import RequestExecutor
from .tweet.conversation_tweet_stream import ConversationTweetStream
from .tweet.tweet import Tweet, TweetId, User, UserId
from .tweet.tweet_stream import TweetStream

try:
    # File is auto-generated. See "make build-versionpy".
    from .version import __version__  # type: ignore
except ImportError:
    __version__ = "dev"

__version_info__ = tuple(
    (int(part) if part.isdigit() else part)
    for part in __version__.split(".", maxsplit=4)
)

__all__ = [
    "main",
    "ConversationRequest",
    "Replies",
    "DEFAULT_BATCH_SIZE",
    "DEFAULT_MAX_TWEETS",
    "Request",
    "DEFAULT_FILTER",
    "Search",
    "SearchFilter",
    "Thread",
    "RequestExecutor",
    "ConversationTweetStream",
    "Tweet",
    "TweetId",
    "User",
    "UserId",
    "TweetStream",
    "__version__",
    "__version_info__",
]
