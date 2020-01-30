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

from pathlib import Path
from typing import Optional

from nasty.request.request import Request
from nasty.tweet.tweet import Tweet
from nasty.tweet.tweet_stream import TweetStream


class MockRequestContext:
    RESULT_TWEET = Tweet({})

    def __init__(self, *, num_results: int = 0):
        self.request: Optional[Request] = None
        self.remaining_result_tweets = num_results

        outer_self = self

        class MockTweetStream(TweetStream):
            def __next__(self) -> Tweet:
                if outer_self.remaining_result_tweets:
                    outer_self.remaining_result_tweets -= 1
                    return outer_self.RESULT_TWEET
                raise StopIteration()

        def mock_request(request: Request) -> TweetStream:
            self.request = request
            if request.max_tweets:
                self.remaining_result_tweets = min(
                    self.remaining_result_tweets, request.max_tweets
                )
            return MockTweetStream()

        self.mock_request = mock_request


class MockBatchContext:
    def __init__(self) -> None:
        self.load_args = None
        self.execute_args = None

        class MockBatch:
            @staticmethod
            def load(file: Path) -> None:
                self.load_args = (file,)

            @staticmethod
            def execute(results_dir: Optional[Path]) -> None:
                self.execute_args = (results_dir,)

        self.MockBatch = MockBatch


class MockBatchResultsContext:
    def __init__(self) -> None:
        self.init_args = None
        self.idify_args = None
        self.unidify_args = None

        class MockBatchResults:
            @staticmethod
            def __init__(results_dir: Path):
                self.init_args = (results_dir,)

            @staticmethod
            def idify(results_dir: Path) -> None:
                self.idify_args = (results_dir,)

            @staticmethod
            def unidify(results_dir: Path) -> None:
                self.unidify_args = (results_dir,)

        self.MockBatchResults = MockBatchResults
