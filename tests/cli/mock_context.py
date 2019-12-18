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

from typing import Generic, Optional, TypeVar

from nasty.request.request import Request
from nasty.tweet.tweet import Tweet
from nasty.tweet.tweet_stream import TweetStream

_T_Request = TypeVar("_T_Request", bound=Request)


class MockContext(Generic[_T_Request]):
    RESULT_TWEET = Tweet({})

    def __init__(self, *, num_results: int = 0):
        self.request: Optional[_T_Request] = None
        self.remaining_result_tweets = num_results

        outer_self = self

        class MockTweetStream(TweetStream):
            def __next__(self) -> Tweet:
                if outer_self.remaining_result_tweets:
                    outer_self.remaining_result_tweets -= 1
                    return outer_self.RESULT_TWEET
                raise StopIteration()

        def mock_request(request: _T_Request) -> TweetStream:
            self.request = request
            if request.max_tweets:
                self.remaining_result_tweets = min(
                    self.remaining_result_tweets, request.max_tweets
                )
            return MockTweetStream()

        self.mock_request = mock_request
