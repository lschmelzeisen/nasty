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

from argparse import ArgumentParser, _ArgumentGroup
from typing import Sequence

from .._util.time_ import yyyy_mm_dd_date
from ..request.search import DEFAULT_FILTER, Search, SearchFilter
from ..request_executor import RequestExecutor
from ._request_command import _RequestCommand


class _SearchCommand(_RequestCommand[Search]):
    @classmethod
    def command(cls) -> str:
        return "search"

    @classmethod
    def aliases(cls) -> Sequence[str]:
        return ["s"]

    @classmethod
    def description(cls) -> str:
        return "Retrieve Tweets using the Twitter advanced search."

    @classmethod
    def _config_request_subclass_args(cls, argparser: ArgumentParser) -> _ArgumentGroup:
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
            help="Earliest date for Tweets (inclusive) as YYYY-MM-DD.",
        )
        g.add_argument(
            "-u",
            "--until",
            metavar="<DATE>",
            type=yyyy_mm_dd_date,
            help="Latest date for Tweets (exclusive) as YYYY-MM-DD.",
        )
        g.add_argument(
            "-f",
            "--filter",
            metavar="<FILTER>",
            type=SearchFilter.__getitem__,
            default=DEFAULT_FILTER,
            help=(
                "Sorting/filtering of Tweets (TOP, LATEST, PHOTOS, VIDEOS). Defaults "
                "to 'TOP'."
            ),
        )
        g.add_argument(
            "-l",
            "--lang",
            metavar="<LANG>",
            default="en",
            help="Two-letter language code for Tweets. Defaults to 'en'.",
        )
        return g

    @classmethod
    def _config_executor_args(cls, argparser: ArgumentParser) -> _ArgumentGroup:
        g = super()._config_executor_args(argparser)
        g.add_argument(
            "-d",
            "--daily",
            action="store_true",
            help=(
                "For a request with since and until date, submit one search request "
                "per day in the date-range with identical settings otherwise."
            ),
        )
        return g

    def validate_arguments(self, argparser: ArgumentParser) -> None:
        super().validate_arguments(argparser)
        if self._args.daily:
            if not self._args.to_executor:
                argparser.error("-d (--daily) requires -e (--to-executor).")

            if self._args.since is None or self._args.until is None:
                argparser.error("-d (--daily) requires -s (--since) and -u (--until).")

    def _request_executor_submit(
        self, request_executor: RequestExecutor, request: Search
    ) -> None:
        if self._args.daily:
            for daiy_request in request.to_daily_requests():
                request_executor.submit(daiy_request)
        else:
            request_executor.submit(request)

    def build_request(self) -> Search:
        return Search(
            self._args.query,
            since=self._args.since,
            until=self._args.until,
            filter_=self._args.filter,
            lang=self._args.lang,
            max_tweets=self._args.max_tweets,
            batch_size=self._args.batch_size,
        )
