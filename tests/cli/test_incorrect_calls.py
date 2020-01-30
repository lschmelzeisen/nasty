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
from logging import getLogger

import pytest
from _pytest.capture import CaptureFixture

from nasty.cli.main import main

logger = getLogger(__name__)


@pytest.mark.parametrize(
    "args_string",
    [
        "trump",
        "332308211321425920",
        "search trump",
        "search --query trump --since 2019",
        "search --query trump --until 2019",
        "search --query trump --filter latest",
        "search --query trump --max-tweets five",
        "search --query trump --batch-size 3.0",
        "search --query trump --to-batch",
        "search --query trump --daily",
        "search --query trump --to-batch file --daily",
        "search --query trump --since 2019-03-21 --to-batch file --daily",
        "search --query trump --until 2019-03-21 --to-batch file --daily",
        "replies 332308211321425920",
        "replies --tweet-id 332308211321425920 --max-tweets five",
        "replies --tweet-id 332308211321425920 --batch-size 3.0",
        "replies --tweet-id 332308211321425920 --to-batch",
        "thread 332308211321425920",
        "thread --tweet-id 332308211321425920 --max-tweets five",
        "thread --tweet-id 332308211321425920 --batch-size 3.0",
        "thread --tweet-id 332308211321425920 --to-batch",
        "batch",
        "batch --batch-file",
        "batch --batch-file batch.jsonl",
        "batch --batch-file batch.jsonl --results-dir",
        "batch --results-dir",
        "batch --batch-file --results-dir out/",
        "idify --in-dir",
        "idify --out-dir",
        "idify --out-dir out/",
        "unidify --in-dir",
        "unidify --out-dir",
        "unidify --out-dir out/",
    ],
    ids=repr,
)
def test_incorrect_calls(args_string: str, capsys: CaptureFixture) -> None:
    args = args_string.split(" ") if args_string != "" else []
    logger.debug("Raw arguments: {}".format(args))

    with pytest.raises(SystemExit) as excinfo:
        main(args)

    assert excinfo.value.code == 2

    captured = capsys.readouterr().err
    logger.debug("Captured Error:")
    for line in captured.split("\n"):
        logger.debug("  " + line)
    assert captured.startswith("usage: nasty ")
    assert ": error: " in captured
