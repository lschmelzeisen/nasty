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

import json
from datetime import date
from logging import getLogger
from pathlib import Path
from typing import Any, Mapping, Sequence

import pytest
from _pytest.capture import CaptureFixture
from _pytest.monkeypatch import MonkeyPatch

from nasty.cli.main import main
from nasty.request.search import Search, SearchFilter
from nasty.request_executor import _Job

from .mock_context import MockContext

logger = getLogger(__name__)

SEARCH_KWARGS = [
    {"query": "trump"},
    {"query": "donald trump"},
    {"query": "trump", "since": date(2019, 3, 21), "until": date(2019, 3, 22)},
    {"query": "trump", "filter_": SearchFilter.LATEST},
    {"query": "trump", "lang": "de"},
    {"query": "trump", "max_tweets": 17, "batch_size": 71},
]


def _make_args_from_search_kwargs(search_kwargs: Mapping[str, Any]) -> Sequence[str]:
    args = ["search", "--query", search_kwargs["query"]]
    if "since" in search_kwargs:
        args.extend(["--since", search_kwargs["since"].strftime("%Y-%m-%d")])
    if "until" in search_kwargs:
        args.extend(["--until", search_kwargs["until"].strftime("%Y-%m-%d")])
    if "filter_" in search_kwargs:
        args.extend(["--filter", search_kwargs["filter_"].name])
    if "lang" in search_kwargs:
        args.extend(["--lang", search_kwargs["lang"]])
    if "max_tweets" in search_kwargs:
        args.extend(["--max-tweets", str(search_kwargs["max_tweets"])])
    if "batch_size" in search_kwargs:
        args.extend(["--batch-size", str(search_kwargs["batch_size"])])
    return args


@pytest.mark.parametrize("search_kwargs", SEARCH_KWARGS, ids=repr)
def test_correct_call(
    search_kwargs: Mapping[str, Any], monkeypatch: MonkeyPatch, capsys: CaptureFixture
) -> None:
    mock_context: MockContext[Search] = MockContext()
    monkeypatch.setattr(Search, "request", mock_context.mock_request)

    main(_make_args_from_search_kwargs(search_kwargs))

    assert mock_context.tweet_stream_next_called
    assert mock_context.request == Search(**search_kwargs)
    assert capsys.readouterr().out == ""


@pytest.mark.parametrize("search_kwargs", SEARCH_KWARGS, ids=repr)
def test_correct_call_to_executor(
    search_kwargs: Mapping[str, Any], capsys: CaptureFixture, tmp_path: Path,
) -> None:
    executor_file = tmp_path / "jobs.jsonl"
    args = list(_make_args_from_search_kwargs(search_kwargs))
    args.extend(["--to-executor", str(executor_file)])
    main(args)

    assert capsys.readouterr().out == ""
    with executor_file.open("r", encoding="UTF-8") as fin:
        job = _Job.from_json(json.load(fin))
        assert job.request == Search(**search_kwargs)
        assert job._id
        assert job.completed_at is None
        assert job.exception is None


def test_correct_call_to_executor_daily(capsys: CaptureFixture, tmp_path: Path) -> None:
    executor_file = tmp_path / "jobs.jsonl"
    args = [
        "search",
        "--query",
        "trump",
        "--since",
        "2019-01-01",
        "--until",
        "2019-02-01",
        "--to-executor",
        str(executor_file),
        "--daily",
    ]
    main(args)

    assert capsys.readouterr().out == ""
    with executor_file.open("r", encoding="UTF-8") as fin:
        for line, expected_request in zip(
            fin,
            Search(
                "trump", since=date(2019, 1, 1), until=date(2019, 2, 1)
            ).to_daily_requests(),
        ):
            job = _Job.from_json(json.loads(line))
            assert job.request == expected_request
            assert job._id
            assert job.completed_at is None
            assert job.exception is None


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
        "--query trump --to-executor",
        "--query trump --daily",
        "--query trump --to-executor file --daily",
        "--query trump --since 2019-03-21 --to-executor file --daily",
        "--query trump --until 2019-03-21 --to-executor file --daily",
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
