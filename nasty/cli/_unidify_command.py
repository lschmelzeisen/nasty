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
from argparse import ArgumentParser
from pathlib import Path
from sys import stdin
from typing import Sequence

from overrides import overrides

from .._util.tweepy_ import statuses_lookup
from ..batch.batch_results import BatchResults
from ..tweet.tweet import TweetId
from ._command import _Command


class _UnidifyCommand(_Command):
    @classmethod
    @overrides
    def command(cls) -> str:
        return "unidify"

    @classmethod
    @overrides
    def aliases(cls) -> Sequence[str]:
        return ["u", "unid"]

    @classmethod
    @overrides
    def description(cls) -> str:
        return (
            "Collect full Tweet information from Tweet-IDs (via official Twitter API)."
        )

    @classmethod
    def config_argparser(cls, argparser: ArgumentParser) -> None:
        g = argparser.add_argument_group(
            "Unidify Arguments",
            "By default Tweet-IDs are read line-by-line from stdin and collected "
            "Tweets are written to stdout. Use the following arguments to instead "
            "operate on idified batch results.",
        )
        g.add_argument(
            "-i",
            "--in-dir",
            metavar="<DIR>",
            type=Path,
            help="Directory with idified batch results.",
        )
        g.add_argument(
            "-o",
            "--out-dir",
            metavar="<DIR>",
            type=Path,
            help="Directory to which unidified batch results will be written. If not "
            "given, will use input directory.",
        )

    @overrides
    def validate_arguments(self, argparser: ArgumentParser) -> None:
        if self._args.out_dir and not self._args.in_dir:
            argparser.error("-o (--out-dir) requires -i (--in-dir).")

    @overrides
    def run(self) -> None:
        in_dir = self._args.in_dir
        out_dir = self._args.out_dir

        if in_dir:
            if out_dir is None:
                out_dir = in_dir

            batch_results = BatchResults(in_dir)
            batch_results.unidify(out_dir)

        else:
            for tweet in statuses_lookup(TweetId(line.strip()) for line in stdin):
                if tweet is not None:
                    print(json.dumps(tweet.to_json()))  # noqa T001
