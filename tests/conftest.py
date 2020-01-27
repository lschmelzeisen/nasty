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

import logging
from typing import Iterator

import pytest
from _pytest.config import Config
from _pytest.fixtures import FixtureRequest
from _pytest.monkeypatch import MonkeyPatch

from .util.requests_cache import RequestsCache


def pytest_configure(config: Config) -> None:
    _configure_logging(config)
    _configure_pycharm(config)
    _configure_requests_cache(config)


def _configure_logging(config: Config) -> None:
    logging.addLevelName(logging.WARNING, "WARN")
    logging.addLevelName(logging.CRITICAL, "CRIT")

    config.option.log_level = "DEBUG"
    config.option.log_format = (
        "%(asctime)s %(levelname)-5.5s [ %(name)-31s ] %(message)s"
    )


def _configure_pycharm(config: Config) -> None:
    # When running pytest from PyCharm enable live cli logging so that we can click a
    # test case and see (only) its log output. When not using PyCharm, this
    # functionality is available via the html report.
    if config.pluginmanager.hasplugin("teamcity.pytest_plugin"):
        config.option.log_cli_level = "DEBUG"


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
