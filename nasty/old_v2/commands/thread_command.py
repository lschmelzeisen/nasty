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

from argparse import ArgumentParser
from typing import List

from nasty.old_v2.commands import TimelineCommand
from nasty.retrieval.thread import Thread
from nasty.retrieval.timeline import Timeline


class ThreadCommand(TimelineCommand):
    @classmethod
    def command(cls) -> str:
        return "thread"

    @classmethod
    def aliases(cls) -> List[str]:
        return ["t"]

    @classmethod
    def description(cls) -> str:
        return "Retrieve all Tweets threaded under a Tweet."

    @classmethod
    def _config_retrieval_args(cls, argparser: ArgumentParser) -> None:
        g = argparser.add_argument_group(
            "Thread Arguments",
            "Control to which Tweet threaded Tweets are " "retrieved.",
        )
        g.add_argument(
            "-t",
            "--tweet-id",
            metavar="<ID>",
            type=str,
            required=True,
            help="ID of the Tweet to retrieve " "threaded Tweets for (required).",
        )

    def setup_retrieval(self) -> Timeline:
        return Thread(self._args.tweet_id, self._args.max_tweets, self._args.batch_size)
