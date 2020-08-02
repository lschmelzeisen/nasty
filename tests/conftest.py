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

from typing import Iterator

import pytest
from _pytest.config import Config
from _pytest.fixtures import FixtureRequest
from _pytest.monkeypatch import MonkeyPatch
from nasty_utils import LoggingSettings

from nasty._settings import NastySettings

from .util.requests_cache import RequestsCache


def pytest_configure(config: Config) -> None:
    LoggingSettings.setup_pytest_logging(config)
    _configure_requests_cache(config)


def _configure_requests_cache(config: Config) -> None:
    config.addinivalue_line(
        "markers", "requests_cache_disabled: Disable caching of requests."
    )
    config.addinivalue_line(
        "markers", "requests_cache_regenerate: Regenerate requested cached requests."
    )


@pytest.fixture(scope="session")
def requests_cache() -> Iterator[RequestsCache]:
    with RequestsCache() as requests_cache:
        yield requests_cache


@pytest.fixture(scope="session")
def settings() -> Iterator[NastySettings]:
    settings = NastySettings.find_and_load_from_settings_file()
    yield settings


@pytest.fixture(autouse=True)
def activate_requests_cache(
    request: FixtureRequest, monkeypatch: MonkeyPatch, requests_cache: RequestsCache
) -> None:
    if not request.node.get_closest_marker("requests_cache_disabled"):
        requests_cache.activate(
            monkeypatch,
            bool(request.node.get_closest_marker("requests_cache_regenerate")),
        )


@pytest.fixture(autouse=True)
def disrespect_robotstxt(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("NASTY_DISRESPECT_ROBOTSTXT", "1")
