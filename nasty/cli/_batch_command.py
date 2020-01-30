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

from argparse import ArgumentParser
from pathlib import Path
from typing import Sequence

from overrides import overrides

from ..batch.batch import Batch
from ._command import _Command


class _BatchCommand(_Command):
    @classmethod
    @overrides
    def command(cls) -> str:
        return "batch"

    @classmethod
    @overrides
    def aliases(cls) -> Sequence[str]:
        return ["b"]

    @classmethod
    @overrides
    def description(cls) -> str:
        return "Execute previously created batch of requests."

    @classmethod
    @overrides
    def config_argparser(cls, argparser: ArgumentParser) -> None:
        g = argparser.add_argument_group(
            "Batch Arguments",
            "Requests can be appended to a batch file by using the -b (--to-batch) "
            "options of the other nasty commands and then executed via this command. "
            "This allows to operate in batch mode, track progress, and rerun "
            "uncompleted/failed requests.",
        )
        g.add_argument(
            "-b",
            "--batch-file",
            metavar="<FILE>",
            type=Path,
            required=True,
            help="Batch file to which requests have been appended.",
        )
        g.add_argument(
            "-r",
            "--results-dir",
            metavar="<DIR>",
            type=Path,
            required=True,
            help="Directory to which results will be written.",
        )

    @overrides
    def run(self) -> None:
        batch = Batch()
        batch.load(self._args.batch_file)
        batch.execute(self._args.results_dir)
