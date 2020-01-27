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

from datetime import date, timedelta
from typing import Mapping, Tuple, Type

import pytest

from nasty.request.replies import Replies
from nasty.request.request import Request
from nasty.request.search import Search
from nasty.request.thread import Thread


@pytest.mark.parametrize(
    "args",
    [
        (Search, {"query": "q", "max_tweets": 0}),
        (Search, {"query": "q", "max_tweets": -1}),
        (Search, {"query": "q", "batch_size": 0}),
        (Search, {"query": "q", "batch_size": -1}),
        (Search, {"query": "q", "since": date(2010, 1, 1), "until": date(2010, 1, 1)}),
        (Search, {"query": "q", "since": date(2010, 1, 2), "until": date(2010, 1, 1)}),
    ],
    ids=lambda args: args[0].__name__ + ": " + repr(args[1]),
)
def test_illegal_args(args: Tuple[Type[Request], Mapping[str, object]]) -> None:
    type_, kwargs = args
    with pytest.raises(ValueError):
        type_(**kwargs)


@pytest.mark.parametrize(
    "request_",
    [
        Search("q"),
        Replies("332308211321425920", max_tweets=None),
        Thread("332308211321425920", max_tweets=123, batch_size=456),
    ],
    ids=repr,
)
def test_json_conversion(request_: Request) -> None:
    assert request_ == request_.from_json(request_.to_json())


@pytest.mark.parametrize(
    "search", [Search("q", since=date(2010, 1, 1), until=date(2010, 2, 1))], ids=repr,
)
def test_search_to_daily_requests(search: Search) -> None:
    # assert is not None necessary for mypy type checking
    daily_requests = search.to_daily_requests()
    assert search.since is not None and search.until is not None
    assert (search.until - search.since).days == len(daily_requests)
    for daily_request in daily_requests:
        assert daily_request.since is not None and daily_request.until is not None
        assert timedelta(days=1) == daily_request.until - daily_request.since


@pytest.mark.parametrize(
    "search",
    [
        Search("q"),
        Search("q", since=date(2010, 1, 1)),
        Search("q", until=date(2010, 1, 1)),
    ],
    ids=repr,
)
def test_search_into_daily_requests_illegal_args(search: Search) -> None:
    with pytest.raises(ValueError):
        search.to_daily_requests()
