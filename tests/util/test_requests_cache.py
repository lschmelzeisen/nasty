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

from http import HTTPStatus
from logging import getLogger
from timeit import timeit

import pytest
from requests import Session

logger = getLogger(__name__)
time_without_cache = None
time_with_cache = None


def _perform_request() -> None:
    with Session() as session:
        response = session.get("https://example.org")
    assert HTTPStatus(response.status_code) == HTTPStatus.OK


@pytest.mark.requests_cache_regenerate
def test_request_without_cache() -> None:
    global time_without_cache
    time_without_cache = timeit(_perform_request, number=1)


def test_request_with_cache() -> None:
    global time_with_cache
    time_with_cache = timeit(_perform_request, number=1)


def test_with_cache_faster() -> None:
    global time_without_cache, time_with_cache
    assert time_without_cache is not None
    assert time_with_cache is not None
    logger.debug(
        "Request took {:.4f}s without cache and {:.4f}s with cache.".format(
            time_without_cache, time_with_cache
        )
    )

    # Expect at least a 5x speedup through caching requests.
    assert time_without_cache > 5 * time_with_cache
