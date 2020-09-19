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

import json
import sys
from datetime import date
from pathlib import Path
from typing import Mapping, Optional

from nasty_utils import (
    Argument,
    ArgumentGroup,
    Program,
    ProgramConfig,
    checked_cast,
    parse_yyyy_mm_dd,
)
from overrides import overrides
from pydantic import validator

import nasty
from nasty._settings import NastySettings
from nasty._util.tweepy_ import statuses_lookup
from nasty.batch.batch import Batch
from nasty.batch.batch_results import BatchResults
from nasty.request.replies import Replies
from nasty.request.request import DEFAULT_BATCH_SIZE, Request
from nasty.request.search import DEFAULT_FILTER, Search, SearchFilter
from nasty.request.thread import Thread
from nasty.tweet.tweet import Tweet, TweetId

# TODO: Order Argument Groups


_REQUEST_ARGUMENT_GROUP = ArgumentGroup(
    name="Request Arguments",
    description="Control how Tweets are requested.",
)
_BATCH_ARGUMENT_GROUP = ArgumentGroup(
    name="Batch Arguments",
    description=(
        "NASTY supports storing requests in a batch file and executing them later via "
        "the 'nasty batch' command, which allows to operate in batch mode, track "
        "progress, and rerun uncompleted/failed requests."
    ),
)


class RequestProgram(Program):
    max_tweets: Optional[int] = Argument(
        100,
        alias="max-tweets",
        short_alias="n",
        description=(
            "Maximum number of tweets to retrieve. Set to -1 to receive as many as "
            "possible. Defaults to 100."
        ),
        metavar="N",
        group=_REQUEST_ARGUMENT_GROUP,
    )

    @validator("max_tweets")
    def _max_tweets_validator(cls, v: Optional[int]) -> Optional[int]:  # noqa: N805
        return v if v != -1 else None

    batch_size: int = Argument(
        -1,
        alias="batch-size",
        short_alias="i",
        description=(
            "Batch size to retrieve Tweets in. Set to -1 for default behavior. Only "
            "change when necessary."
        ),
        metavar="N",
        group=_REQUEST_ARGUMENT_GROUP,
    )

    @validator("batch_size")
    def _batch_size_validator(cls, v: int) -> int:  # noqa: N805
        return v if v != -1 else DEFAULT_BATCH_SIZE

    to_batch: Optional[Path] = Argument(
        alias="to-batch",
        short_alias="b",
        description="Append request to batch file instead of executing.",
        metavar="FILE",
        group=_BATCH_ARGUMENT_GROUP,
    )

    @overrides
    def run(self) -> None:
        request = self._build_request()
        if self.to_batch:
            batch = Batch()
            if self.to_batch.exists():
                batch.load(self.to_batch)
            self._batch_submit(batch, request)
            batch.dump(self.to_batch)
        else:
            for tweet in request.request():
                sys.stdout.write(json.dumps(tweet.to_json()) + "\n")

    def _build_request(self) -> Request:
        raise NotImplementedError()

    def _batch_submit(self, batch: Batch, request: Request) -> None:
        batch.append(request)


_SEARCH_ARGUMENT_GROUP = ArgumentGroup(
    name="Search Arguments", description="Control what kind of Tweets are searched."
)


class SearchProgram(RequestProgram):
    class Config(ProgramConfig):
        title = "search"
        aliases = ("s",)
        description = "Retrieve Tweets using the Twitter advanced search."

    settings: NastySettings = Argument(
        alias="config", description="Overwrite default config file path."
    )

    query: str = Argument(
        short_alias="q",
        description="Search string (required).",
        group=_SEARCH_ARGUMENT_GROUP,
    )

    since: Optional[date] = Argument(
        short_alias="s",
        description="Earliest date for Tweets (inclusive) as YYYY-MM-DD.",
        metavar="DATE",
        group=_SEARCH_ARGUMENT_GROUP,
    )

    @validator("since", pre=True)
    def _since_validator(cls, v: Optional[str]) -> Optional[date]:  # noqa: N805
        return parse_yyyy_mm_dd(v) if v else None

    until: Optional[date] = Argument(
        short_alias="u",
        description="Latest date for Tweets (exclusive) as YYYY-MM-DD.",
        metavar="DATE",
        group=_SEARCH_ARGUMENT_GROUP,
    )

    @validator("until", pre=True, always=False)
    def _until_validator(cls, v: Optional[str]) -> Optional[date]:  # noqa: N805
        return parse_yyyy_mm_dd(v) if v else None

    filter_: SearchFilter = Argument(
        DEFAULT_FILTER,
        alias="filter",
        short_alias="f",
        description=(
            "Sorting/filtering of Tweets (top, latest, photos, videos). Defaults "
            "to 'top'."
        ),
        group=_SEARCH_ARGUMENT_GROUP,
    )

    lang: str = Argument(
        "en",
        short_alias="l",
        description=(
            "Language for Tweets, presumably as ISO 3166-1 two or three letter codes. "
            "Defaults to 'en'."
        ),
        group=_SEARCH_ARGUMENT_GROUP,
    )

    daily: bool = Argument(
        False,
        short_alias="d",
        description=(
            "For a request with since and until date, append one search request "
            "per day in the date-range with identical settings otherwise."
        ),
        group=_BATCH_ARGUMENT_GROUP,
    )

    @validator("daily")
    def _daily_validator(
        cls, v: bool, values: Mapping[str, object]  # noqa:N805
    ) -> bool:
        if v and not values["to_batch"]:
            raise ValueError("-d/--daily requires -b/--to-batch.")
        if v and (values["since"] is None or values["until"] is None):
            raise ValueError("-d/--daily requires -s/--since and -u/--until.")
        return v

    @overrides
    def _build_request(self) -> Search:
        return Search(
            self.query,
            since=self.since,
            until=self.until,
            filter_=self.filter_,
            lang=self.lang,
            max_tweets=self.max_tweets,
            batch_size=self.batch_size,
        )

    @overrides
    def _batch_submit(self, batch: Batch, request: Request) -> None:
        request = checked_cast(Search, request)
        if self.daily:
            for daily_request in request.to_daily_requests():
                super()._batch_submit(batch, daily_request)
        else:
            super()._batch_submit(batch, request)


_REPLIES_ARGUMENT_GROUP = ArgumentGroup(
    name="Replies Arguments",
    description="Control to which Tweet replies are retrieved.",
)


class RepliesProgram(RequestProgram):
    class Config(ProgramConfig):
        title = "replies"
        aliases = ("r",)
        description = "Retrieve all directly replying Tweets to a Tweet."

    settings: NastySettings = Argument(
        alias="config", description="Overwrite default config file path."
    )

    tweet_id: TweetId = Argument(
        alias="tweet-id",
        short_alias="t",
        description="ID of the Tweet to retrieve replies for (required).",
        metavar="ID",
        group=_REPLIES_ARGUMENT_GROUP,
    )

    @overrides
    def _build_request(self) -> Request:
        return Replies(
            self.tweet_id, max_tweets=self.max_tweets, batch_size=self.batch_size
        )


_THREAD_ARGUMENT_GROUP = ArgumentGroup(
    name="Thread Arguments",
    description="Control to which Tweet's threaded Tweets are retrieved.",
)


class ThreadProgram(RequestProgram):
    class Config(ProgramConfig):
        title = "thread"
        aliases = ("t",)
        description = "Retrieve all Tweets threaded under a Tweet."

    settings: NastySettings = Argument(
        alias="config", description="Overwrite default config file path."
    )

    tweet_id: TweetId = Argument(
        alias="tweet-id",
        short_alias="t",
        description="ID of the Tweet to retrieve threaded Tweets for (required).",
        metavar="ID",
        group=_THREAD_ARGUMENT_GROUP,
    )

    @overrides
    def _build_request(self) -> Request:
        return Thread(
            self.tweet_id, max_tweets=self.max_tweets, batch_size=self.batch_size
        )


_BATCH_ARGUMENT_GROUP = ArgumentGroup(
    name="Batch Arguments",
    description="Execute previously created batch of requests.",
)


class BatchProgram(Program):
    class Config(ProgramConfig):
        title = "batch"
        aliases = ("b",)
        description = "Execute previously created batch of requests."

    settings: NastySettings = Argument(
        alias="config", description="Overwrite default config file path."
    )

    batch_file: Path = Argument(
        alias="batch-file",
        short_alias="b",
        description="Batch file to which requests have been appended.",
        metavar="FILE",
        group=_BATCH_ARGUMENT_GROUP,
    )

    results_dir: Path = Argument(
        alias="results-dir",
        short_alias="r",
        description="Directory to which results will be written.",
        metavar="DIR",
        group=_BATCH_ARGUMENT_GROUP,
    )

    @overrides
    def run(self) -> None:
        batch = Batch()
        batch.load(self.batch_file)
        batch.execute(self.results_dir)


_IDIFY_ARGUMENT_GROUP = ArgumentGroup(
    name="Idifiy Arguments",
    description=(
        "By default Tweets are read line-by-line from stdin and the corresponding "
        "Tweet-IDs are written to stdout. Use the following arguments to instead "
        "operate on a result directory of a batch of requests."
    ),
)


class IdifyProgram(Program):
    class Config(ProgramConfig):
        title = "idify"
        aliases = ("i", "id")
        description = "Reduce Tweet-collection to Tweet-IDs (for publishing)."

    settings: NastySettings = Argument(
        alias="config", description="Overwrite default config file path."
    )

    in_dir: Optional[Path] = Argument(
        alias="in-dir",
        short_alias="i",
        description="Directory with results of a batch of requests.",
        metavar="DIR",
        group=_IDIFY_ARGUMENT_GROUP,
    )

    out_dir: Optional[Path] = Argument(
        alias="out-dir",
        short_alias="o",
        description=(
            "Directory to which Tweet-IDs will be written. If not given, will use "
            "input directory."
        ),
        metavar="DIR",
        group=_IDIFY_ARGUMENT_GROUP,
    )

    @validator("out_dir")
    def _out_dir_validator(
        cls, v: Optional[Path], values: Mapping[str, object]  # noqa: N805
    ) -> Optional[Path]:
        if v and not values["in_dir"]:
            raise ValueError("-o/--out-dir requires -i/--in-dir.")
        return v

    @overrides
    def run(self) -> None:
        if self.in_dir:
            batch_results = BatchResults(self.in_dir)
            batch_results.idify(self.out_dir if self.out_dir else self.in_dir)
        else:
            for line in sys.stdin:
                sys.stdout.write(str(Tweet(json.loads(line)).id) + "\n")


_UNIDIFY_ARGUMENT_GROUP = ArgumentGroup(
    name="Unidify Arguments",
    description=(
        "By default Tweet-IDs are read line-by-line from stdin and collected Tweets "
        "are written to stdout. Use the following arguments to instead operate on "
        "idified batch results."
    ),
)


class UnidifyProgram(Program):
    class Config(ProgramConfig):
        title = "unidify"
        aliases = ("u", "unid")
        description = (
            "Collect full Tweet information from Tweet-IDs (via official Twitter API)."
        )

    settings: NastySettings = Argument(
        alias="config", description="Overwrite default config file path."
    )

    in_dir: Optional[Path] = Argument(
        alias="in-dir",
        short_alias="i",
        description="Directory with idified batch results.",
        metavar="DIR",
        group=_UNIDIFY_ARGUMENT_GROUP,
    )

    out_dir: Optional[Path] = Argument(
        alias="out-dir",
        short_alias="o",
        description=(
            "Directory to which unidified batch results will be written. If not "
            "given, will use input directory."
        ),
        metavar="DIR",
        group=_UNIDIFY_ARGUMENT_GROUP,
    )

    @validator("out_dir")
    def _out_dir_validator(
        cls, v: Optional[Path], values: Mapping[str, object]  # noqa: N805
    ) -> Optional[Path]:
        if v and not values["in_dir"]:
            raise ValueError("-o/--out-dir requires -i/--in-dir.")
        return v

    @overrides
    def run(self) -> None:
        if self.in_dir:
            batch_results = BatchResults(self.in_dir)
            batch_results.unidify(
                self.settings.twitter_api,
                self.out_dir if self.out_dir else self.in_dir,
            )
        else:
            for tweet in statuses_lookup(
                (TweetId(line.strip()) for line in sys.stdin), self.settings.twitter_api
            ):
                if tweet is not None:
                    sys.stdout.write(json.dumps(tweet.to_json()) + "\n")


class NastyProgram(Program):
    class Config(ProgramConfig):
        title = "nasty"
        version = nasty.__version__
        description = "NASTY Advanced Search Tweet Yielder."
        subprograms = (
            SearchProgram,
            RepliesProgram,
            ThreadProgram,
            BatchProgram,
            IdifyProgram,
            UnidifyProgram,
        )

    settings: NastySettings = Argument(
        alias="config", description="Overwrite default config file path."
    )
