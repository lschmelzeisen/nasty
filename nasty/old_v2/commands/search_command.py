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

from nasty._util.time_ import yyyy_mm_dd_date
from nasty.old_v2.commands import TimelineCommand
from nasty.retrieval.search import Search
from nasty.retrieval.timeline import Timeline


class SearchCommand(TimelineCommand):
    @classmethod
    def command(cls) -> str:
        return "search"

    @classmethod
    def aliases(cls) -> List[str]:
        return ["s"]

    @classmethod
    def description(cls) -> str:
        return "Retrieve Tweets using the Twitter Advanced Search."

    @classmethod
    def _config_retrieval_args(cls, argparser: ArgumentParser) -> None:
        g = argparser.add_argument_group(
            "Search Arguments", "Control what kind of Tweets are searched."
        )
        g.add_argument(
            "-q",
            "--query",
            metavar="<QUERY>",
            type=str,
            required=True,
            help="Search string (required).",
        )
        g.add_argument(
            "-s",
            "--since",
            metavar="<DATE>",
            type=yyyy_mm_dd_date,
            help="Earliest date for Tweets (inclusive).",
        )
        g.add_argument(
            "-u",
            "--until",
            metavar="<DATE>",
            type=yyyy_mm_dd_date,
            help="Latest date for Tweets (exclusive).",
        )
        g.add_argument(
            "-f",
            "--filter",
            metavar="<FILTER>",
            type=Search.Query.Filter.__getitem__,
            default=Search.Query.Filter.DEFAULT_FILTER,
            help="Sorting/filtering of Tweets (TOP, LATEST, PHOTOS, "
            'VIDEOS). Defaults to "TOP".',
        )
        g.add_argument(
            "-l",
            "--lang",
            metavar="<LANG>",
            default="en",
            help="Two-letter language code for Tweets. Defaults to " '"en".',
        )

    def setup_retrieval(self) -> Timeline:
        return Search(
            Search.Query(
                self._args.query,
                self._args.since,
                self._args.until,
                self._args.filter,
                self._args.lang,
            ),
            self._args.max_tweets,
            self._args.batch_size,
        )
