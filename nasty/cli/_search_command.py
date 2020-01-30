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

from .._util.time_ import yyyy_mm_dd_date
from ..batch.batch import Batch
from ..request.search import DEFAULT_FILTER, Search, SearchFilter
from ._request_command import _RequestCommand


class _SearchCommand(_RequestCommand[Search]):
    @classmethod
    @overrides
    def command(cls) -> str:
        return "search"

    @classmethod
    @overrides
    def aliases(cls) -> Sequence[str]:
        return ["s"]

    @classmethod
    @overrides
    def description(cls) -> str:
        return "Retrieve Tweets using the Twitter advanced search."

    @classmethod
    @overrides
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
            type=str,
            choices=[filter_.name for filter_ in SearchFilter],
            default=DEFAULT_FILTER.name,
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
            help="Language for Tweets, presumably as ISO 3166-1 two or three letter "
            "codes. Defaults to 'en'.",
        )
        return g

    @classmethod
    @overrides
    def _config_batch_args(cls, argparser: ArgumentParser) -> _ArgumentGroup:
        g = super()._config_batch_args(argparser)
        g.add_argument(
            "-d",
            "--daily",
            action="store_true",
            help=(
                "For a request with since and until date, append one search request "
                "per day in the date-range with identical settings otherwise."
            ),
        )
        return g

    @overrides
    def validate_arguments(self, argparser: ArgumentParser) -> None:
        super().validate_arguments(argparser)
        if self._args.daily:
            if not self._args.to_batch:
                argparser.error("-d (--daily) requires -b (--to-batch).")

            if self._args.since is None or self._args.until is None:
                argparser.error("-d (--daily) requires -s (--since) and -u (--until).")

    @overrides
    def _batch_submit(self, batch: Batch, request: Search) -> None:
        if self._args.daily:
            for daily_request in request.to_daily_requests():
                super()._batch_submit(batch, daily_request)
        else:
            super()._batch_submit(batch, request)

    @overrides
    def build_request(self) -> Search:
        filter_ = SearchFilter[self._args.filter]
        return Search(
            self._args.query,
            since=self._args.since,
            until=self._args.until,
            filter_=filter_,
            lang=self._args.lang,
            max_tweets=self._args.max_tweets,
            batch_size=self._args.batch_size,
        )
