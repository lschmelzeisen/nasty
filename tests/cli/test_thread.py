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
from logging import getLogger
from pathlib import Path
from typing import Any, Mapping, Sequence

import pytest
from _pytest.capture import CaptureFixture
from _pytest.monkeypatch import MonkeyPatch

from nasty.cli.main import main
from nasty.request.request import DEFAULT_BATCH_SIZE
from nasty.request.thread import Thread
from nasty.request_executor import RequestExecutor

from .mock_context import MockContext

logger = getLogger(__name__)

THREAD_KWARGS = [
    {"tweet_id": "332308211321425920"},
    {"tweet_id": "332308211321425920", "max_tweets": 17, "batch_size": 71},
    {
        "tweet_id": "332308211321425920",
        "max_tweets": None,
        "batch_size": DEFAULT_BATCH_SIZE,
    },
]


def _make_args_from_thread_kwargs(thread_kwargs: Mapping[str, Any]) -> Sequence[str]:
    args = ["thread", "--tweet-id", thread_kwargs["tweet_id"]]
    if "max_tweets" in thread_kwargs:
        if thread_kwargs["max_tweets"] is None:
            args.extend(["--max-tweets", "-1"])
        else:
            args.extend(["--max-tweets", str(thread_kwargs["max_tweets"])])
    if "batch_size" in thread_kwargs:
        if thread_kwargs["batch_size"] == DEFAULT_BATCH_SIZE:
            args.extend(["--batch-size", "-1"])
        else:
            args.extend(["--batch-size", str(thread_kwargs["batch_size"])])
    return args


@pytest.mark.parametrize("thread_kwargs", THREAD_KWARGS, ids=repr)
def test_correct_call(
    thread_kwargs: Mapping[str, Any], monkeypatch: MonkeyPatch, capsys: CaptureFixture
) -> None:
    mock_context: MockContext[Thread] = MockContext()
    monkeypatch.setattr(Thread, "request", mock_context.mock_request)

    main(_make_args_from_thread_kwargs(thread_kwargs))

    assert mock_context.request == Thread(**thread_kwargs)
    assert not mock_context.remaining_result_tweets
    assert capsys.readouterr().out == ""


@pytest.mark.parametrize("num_results", [5, 10, 20], ids=repr)
def test_correct_call_results(
    num_results: int, monkeypatch: MonkeyPatch, capsys: CaptureFixture
) -> None:
    mock_context: MockContext[Thread] = MockContext(num_results=num_results)
    monkeypatch.setattr(Thread, "request", mock_context.mock_request)

    main(["thread", "--tweet-id", "332308211321425920", "--max-tweets", "10"])

    assert mock_context.request == Thread("332308211321425920", max_tweets=10)
    assert not mock_context.remaining_result_tweets
    assert capsys.readouterr().out == (
        json.dumps(mock_context.RESULT_TWEET.to_json()) + "\n"
    ) * min(10, num_results)


@pytest.mark.parametrize("thread_kwargs", THREAD_KWARGS, ids=repr)
def test_correct_call_to_executor(
    thread_kwargs: Mapping[str, Any], capsys: CaptureFixture, tmp_path: Path,
) -> None:
    executor_file = tmp_path / "jobs.jsonl"
    args = list(_make_args_from_thread_kwargs(thread_kwargs))
    args.extend(["--to-executor", str(executor_file)])
    main(args)

    assert capsys.readouterr().out == ""
    request_executor = RequestExecutor()
    request_executor.load_requests(executor_file)
    assert len(request_executor._jobs) == 1
    assert request_executor._jobs[0].request == Thread(**thread_kwargs)
    assert request_executor._jobs[0]._id
    assert request_executor._jobs[0].completed_at is None
    assert request_executor._jobs[0].exception is None


def test_correct_call_to_executor_exists(
    capsys: CaptureFixture, tmp_path: Path
) -> None:
    existing_request = Thread("1024287257975566338")
    executor_file = tmp_path / "jobs.jsonl"
    request_executor = RequestExecutor()
    request_executor.submit(existing_request)
    request_executor.dump_requests(executor_file)

    main(
        [
            "thread",
            "--tweet-id",
            "332308211321425920",
            "--to-executor",
            str(executor_file),
        ]
    )

    assert capsys.readouterr().out == ""
    request_executor = RequestExecutor()
    request_executor.load_requests(executor_file)
    assert len(request_executor._jobs) == 2
    for i, job in enumerate(request_executor._jobs):
        assert (
            job.request == existing_request if i == 0 else Thread("332308211321425920")
        )
        assert job._id
        assert job.completed_at is None
        assert job.exception is None


@pytest.mark.parametrize(
    "args_string",
    [
        "",
        "332308211321425920",
        "--tweet-id 332308211321425920 --max-tweets five",
        "--tweet-id 332308211321425920 --batch-size 3.0",
        "--tweet-id 332308211321425920 --to-executor",
    ],
    ids=repr,
)
def test_incorrect_call(args_string: str, capsys: CaptureFixture) -> None:
    args = ["thread"]
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
    assert captured.startswith("usage: nasty thread")
    assert "nasty thread: error" in captured
