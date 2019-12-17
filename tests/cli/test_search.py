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

from datetime import date
from logging import getLogger
from typing import Any, Mapping

import pytest
from _pytest.capture import CaptureFixture
from _pytest.monkeypatch import MonkeyPatch

from nasty.cli.main import main
from nasty.request.search import Search, SearchFilter

from .mock_context import MockContext

logger = getLogger(__name__)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"query": "trump"},
        {"query": "donald trump"},
        {"query": "trump", "since": date(2019, 3, 21), "until": date(2019, 3, 22)},
        {"query": "trump", "filter_": SearchFilter.LATEST},
        {"query": "trump", "lang": "de"},
        {"query": "trump", "max_tweets": 17, "batch_size": 71},
    ],
    ids=repr,
)
def test_correct_call(
    kwargs: Mapping[str, Any], monkeypatch: MonkeyPatch, capsys: CaptureFixture
) -> None:
    mock_context: MockContext[Search] = MockContext()
    monkeypatch.setattr(Search, "request", mock_context.mock_request)

    args = ["search", "--query", kwargs["query"]]
    if "since" in kwargs:
        args.extend(["--since", kwargs["since"].strftime("%Y-%m-%d")])
    if "until" in kwargs:
        args.extend(["--until", kwargs["until"].strftime("%Y-%m-%d")])
    if "filter_" in kwargs:
        args.extend(["--filter", kwargs["filter_"].name])
    if "lang" in kwargs:
        args.extend(["--lang", kwargs["lang"]])
    if "max_tweets" in kwargs:
        args.extend(["--max-tweets", str(kwargs["max_tweets"])])
    if "batch_size" in kwargs:
        args.extend(["--batch-size", str(kwargs["batch_size"])])

    main(args)

    assert mock_context.tweet_stream_next_called
    assert mock_context.request == Search(**kwargs)
    assert capsys.readouterr().out == ""

    assert True


@pytest.mark.parametrize(
    "args_string",
    [
        "",
        "trump",
        "--query trump --since 2019",
        "--query trump --until 2019",
        "--query trump --filter latest",
        "--query trump --max-tweets five",
        "--query trump --batch-size 3.0",
    ],
    ids=repr,
)
def test_incorrect_call(args_string: str, capsys: CaptureFixture) -> None:
    args = ["search"]
    if args_string:
        args.extend(args_string.split(" "))
    logger.debug("Raw arguments: {}".format(args))

    with pytest.raises(SystemExit) as excinfo:
        main(args)

    assert excinfo.value.code == 2

    captured = capsys.readouterr().err
    logger.debug("Captured Error:")
    for line in captured.split("\n"):
        logger.debug("  " + line)
    assert captured.startswith("usage: nasty search")
    assert "nasty search: error" in captured


# TODO: test to-executor
# TODO: test daily
