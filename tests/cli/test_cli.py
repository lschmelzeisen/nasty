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
from typing import List, Mapping, Optional, Sequence, Type

import pytest
from _pytest.capture import CaptureFixture
from _pytest.monkeypatch import MonkeyPatch
from typing_extensions import Final

from nasty.cli.main import main
from nasty.request.replies import Replies
from nasty.request.request import DEFAULT_BATCH_SIZE, DEFAULT_MAX_TWEETS, Request
from nasty.request.search import DEFAULT_FILTER, DEFAULT_LANG, Search, SearchFilter
from nasty.request.thread import Thread
from nasty.request_executor import RequestExecutor

from .mock_context import MockContext

logger = getLogger(__name__)

REQUESTS: Final[Mapping[Type[Request], Sequence[Request]]] = {
    Search: [
        Search("trump"),
        Search("donald trump"),
        Search("trump", since=date(2019, 3, 21), until=date(2019, 3, 22)),
        Search("trump", filter_=SearchFilter.LATEST),
        Search("trump", lang="de"),
        Search("trump", max_tweets=17, batch_size=71),
        Search("trump", max_tweets=None, batch_size=DEFAULT_BATCH_SIZE),
    ],
    Replies: [
        Replies("332308211321425920"),
        Replies("332308211321425920", max_tweets=17, batch_size=71),
        Replies("332308211321425920", max_tweets=None, batch_size=DEFAULT_BATCH_SIZE),
    ],
    Thread: [
        Thread("332308211321425920"),
        Thread("332308211321425920", max_tweets=17, batch_size=71),
        Thread("332308211321425920", max_tweets=None, batch_size=DEFAULT_BATCH_SIZE),
    ],
}
ALL_REQUESTS: Final[Sequence[Request]] = [
    request for requests_for_type in REQUESTS.values() for request in requests_for_type
]


def _make_args(  # noqa: C901
    request: Request, to_executor: Optional[Path] = None, daily: bool = False,
) -> Sequence[str]:
    args: List[str] = []

    if isinstance(request, Search):
        args += ["search", "--query", request.query]
        if request.since:
            args += ["--since", request.since.strftime("%Y-%m-%d")]
        if request.until:
            args += ["--until", request.until.strftime("%Y-%m-%d")]
        if request.filter != DEFAULT_FILTER:
            args += ["--filter", request.filter.name]
        if request.lang != DEFAULT_LANG:
            args += ["--lang", request.lang]

    elif isinstance(request, Replies):
        args += ["replies", "--tweet-id", request.tweet_id]

    elif isinstance(request, Thread):
        args += ["thread", "--tweet-id", request.tweet_id]

    else:
        raise ValueError("Unimplemented Request subclass: {}.".format(type(request)))

    if request.max_tweets is None:
        args += ["--max-tweets", "-1"]
    elif request.max_tweets != DEFAULT_MAX_TWEETS:
        args += ["--max-tweets", str(request.max_tweets)]

    if request.batch_size != DEFAULT_BATCH_SIZE:
        args += ["--batch-size", str(request.batch_size)]

    if to_executor is not None:
        args += ["--to-executor", str(to_executor)]

    if daily:
        if not isinstance(request, Search):
            raise ValueError("daily can only be used together with a Search-request.")
        args += ["--daily"]

    return args


@pytest.mark.parametrize("request_", ALL_REQUESTS, ids=repr)
def test_correct_call(
    request_: Request, monkeypatch: MonkeyPatch, capsys: CaptureFixture
) -> None:
    mock_context: MockContext = MockContext()
    monkeypatch.setattr(type(request_), "request", mock_context.mock_request)

    main(_make_args(request_))

    assert mock_context.request == request_
    assert not mock_context.remaining_result_tweets
    assert capsys.readouterr().out == ""


@pytest.mark.parametrize("num_results", [5, 10, 20], ids=repr)
@pytest.mark.parametrize(
    "request_",
    [
        Search("trump", max_tweets=10),
        Replies("332308211321425920", max_tweets=10),
        Thread("332308211321425920", max_tweets=10),
    ],
    ids=repr,
)
def test_correct_call_results(
    request_: Request,
    num_results: int,
    monkeypatch: MonkeyPatch,
    capsys: CaptureFixture,
) -> None:
    mock_context: MockContext = MockContext(num_results=num_results)
    monkeypatch.setattr(type(request_), "request", mock_context.mock_request)

    main(_make_args(request_))

    assert mock_context.request == request_
    assert not mock_context.remaining_result_tweets
    assert capsys.readouterr().out == (
        json.dumps(mock_context.RESULT_TWEET.to_json()) + "\n"
    ) * min(10, num_results)


@pytest.mark.parametrize("request_", ALL_REQUESTS, ids=repr)
def test_correct_call_to_executor(
    request_: Request, capsys: CaptureFixture, tmp_path: Path,
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


@pytest.mark.parametrize(
    "old_request,new_request",
    [
        (REQUESTS[Search][0], REQUESTS[Search][1]),
        (REQUESTS[Replies][0], REQUESTS[Replies][1]),
        (REQUESTS[Thread][0], REQUESTS[Thread][1]),
    ],
    ids=repr,
)
def test_correct_call_to_executor_exists(
    old_request: Request, new_request: Request, capsys: CaptureFixture, tmp_path: Path,
) -> None:
    executor_file = tmp_path / "jobs.jsonl"
    request_executor = RequestExecutor()
    request_executor.submit(old_request)
    request_executor.dump_requests(executor_file)

    main(_make_args(new_request, to_executor=executor_file))

    assert capsys.readouterr().out == ""
    request_executor = RequestExecutor()
    request_executor.load_requests(executor_file)
    assert len(request_executor._jobs) == 2
    for request, job in zip([old_request, new_request], request_executor._jobs):
        assert job.request == request
        assert job._id
        assert job.completed_at is None
        assert job.exception is None


def test_correct_call_to_executor_daily(capsys: CaptureFixture, tmp_path: Path) -> None:
    executor_file = tmp_path / "jobs.jsonl"
    request = Search("trump", since=date(2019, 1, 1), until=date(2019, 2, 1))

    # Needed for type checking.
    assert request.until is not None and request.since is not None

    main(_make_args(request, to_executor=executor_file, daily=True))

    assert capsys.readouterr().out == ""
    request_executor = RequestExecutor()
    request_executor.load_requests(executor_file)
    assert len(request_executor._jobs) == (request.until - request.since).days
    for job, expected_request in zip(
        request_executor._jobs, request.to_daily_requests()
    ):
        assert job.request == expected_request
        assert job._id
        assert job.completed_at is None
        assert job.exception is None


@pytest.mark.parametrize(
    "args_string",
    [
        "",
        "trump",
        "332308211321425920",
        "search trump",
        "search --query trump --since 2019",
        "search --query trump --until 2019",
        "search --query trump --filter latest",
        "search --query trump --max-tweets five",
        "search --query trump --batch-size 3.0",
        "search --query trump --to-executor",
        "search --query trump --daily",
        "search --query trump --to-executor file --daily",
        "search --query trump --since 2019-03-21 --to-executor file --daily",
        "search --query trump --until 2019-03-21 --to-executor file --daily",
        "replies 332308211321425920",
        "replies --tweet-id 332308211321425920 --max-tweets five",
        "replies --tweet-id 332308211321425920 --batch-size 3.0",
        "replies --tweet-id 332308211321425920 --to-executor",
        "thread 332308211321425920",
        "thread --tweet-id 332308211321425920 --max-tweets five",
        "thread --tweet-id 332308211321425920 --batch-size 3.0",
        "thread --tweet-id 332308211321425920 --to-executor",
    ],
    ids=repr,
)
def test_incorrect_call(args_string: str, capsys: CaptureFixture) -> None:
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
