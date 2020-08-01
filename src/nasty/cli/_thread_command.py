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

from argparse import ArgumentParser, _ArgumentGroup
from typing import Sequence

from overrides import overrides

from ..request.thread import Thread
from ..tweet.tweet import TweetId
from ._request_command import _RequestCommand


class _ThreadCommand(_RequestCommand[Thread]):
    @classmethod
    @overrides
    def command(cls) -> str:
        return "thread"

    @classmethod
    @overrides
    def aliases(cls) -> Sequence[str]:
        return ["t"]

    @classmethod
    @overrides
    def description(cls) -> str:
        return "Retrieve all Tweets threaded under a Tweet."

    @classmethod
    @overrides
    def _config_request_subclass_args(cls, argparser: ArgumentParser) -> _ArgumentGroup:
        g = argparser.add_argument_group(
            "Thread Arguments",
            "Control to which Tweet's threaded Tweets are retrieved.",
        )
        g.add_argument(
            "-t",
            "--tweet-id",
            metavar="<ID>",
            type=TweetId,
            required=True,
            help="ID of the Tweet to retrieve threaded Tweets for (required).",
        )
        return g

    @overrides
    def build_request(self) -> Thread:
        return Thread(
            self._args.tweet_id,
            max_tweets=self._args.max_tweets,
            batch_size=self._args.batch_size,
        )
