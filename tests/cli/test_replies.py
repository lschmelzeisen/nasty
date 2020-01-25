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
from typing import Optional, Sequence

import pytest
from _pytest.capture import CaptureFixture
from _pytest.monkeypatch import MonkeyPatch

from nasty.cli.main import main
from nasty.request.replies import Replies
from nasty.request.request import DEFAULT_BATCH_SIZE, DEFAULT_MAX_TWEETS
from nasty.request_executor import RequestExecutor

from .mock_context import MockContext

logger = getLogger(__name__)

REQUESTS = [
    Replies("332308211321425920"),
    Replies("332308211321425920", max_tweets=17, batch_size=71),
    Replies("332308211321425920", max_tweets=None, batch_size=DEFAULT_BATCH_SIZE),
]


def _make_args(request: Replies, to_executor: Optional[Path] = None) -> Sequence[str]:
    args = ["replies", "--tweet-id", request.tweet_id]
    if request.max_tweets is None:
        args += ["--max-tweets", "-1"]
    elif request.max_tweets != DEFAULT_MAX_TWEETS:
        args += ["--max-tweets", str(request.max_tweets)]
    if request.batch_size != DEFAULT_BATCH_SIZE:
        args += ["--batch-size", str(request.batch_size)]
    if to_executor is not None:
        args += ["--to-executor", str(to_executor)]
    return args


@pytest.mark.parametrize("request_", REQUESTS, ids=repr)
def test_correct_call(
    request_: Replies, monkeypatch: MonkeyPatch, capsys: CaptureFixture
) -> None:
    mock_context: MockContext[Replies] = MockContext()
    monkeypatch.setattr(Replies, "request", mock_context.mock_request)

    main(_make_args(request_))

    assert mock_context.request == request_
    assert not mock_context.remaining_result_tweets
    assert capsys.readouterr().out == ""


@pytest.mark.parametrize("num_results", [5, 10, 20], ids=repr)
def test_correct_call_results(
    num_results: int, monkeypatch: MonkeyPatch, capsys: CaptureFixture
) -> None:
    mock_context: MockContext[Replies] = MockContext(num_results=num_results)
    monkeypatch.setattr(Replies, "request", mock_context.mock_request)
    request = Replies("332308211321425920", max_tweets=10)

    main(_make_args(request))

    assert mock_context.request == request
    assert not mock_context.remaining_result_tweets
    assert capsys.readouterr().out == (
        json.dumps(mock_context.RESULT_TWEET.to_json()) + "\n"
    ) * min(10, num_results)


@pytest.mark.parametrize("request_", REQUESTS, ids=repr)
def test_correct_call_to_executor(
    request_: Replies, capsys: CaptureFixture, tmp_path: Path,
) -> None:
    executor_file = tmp_path / "jobs.jsonl"

    main(_make_args(request_, to_executor=executor_file))

    assert capsys.readouterr().out == ""
    request_executor = RequestExecutor()
    request_executor.load_requests(executor_file)
    assert len(request_executor._jobs) == 1
    assert request_executor._jobs[0].request == request_
    assert request_executor._jobs[0]._id
    assert request_executor._jobs[0].completed_at is None
    assert request_executor._jobs[0].exception is None


def test_correct_call_to_executor_exists(
    capsys: CaptureFixture, tmp_path: Path
) -> None:
    old_request = Replies("1024287257975566338")
    new_request = Replies("332308211321425920")

    executor_file = tmp_path / "jobs.jsonl"
    request_executor = RequestExecutor()
    request_executor.submit(old_request)
    request_executor.dump_requests(executor_file)

    main(_make_args(new_request, to_executor=executor_file))

    assert capsys.readouterr().out == ""
    request_executor = RequestExecutor()
    request_executor.load_requests(executor_file)
    assert len(request_executor._jobs) == 2
    for i, job in enumerate(request_executor._jobs):
        assert job.request == old_request if i == 0 else new_request
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
    args = ["replies"]
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
    assert captured.startswith("usage: nasty replies")
    assert "nasty replies: error" in captured
