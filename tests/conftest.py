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

from logging import INFO, getLogger
from os import environ

import pytest
import urllib3
from _pytest.config import Config
from _pytest.fixtures import FixtureRequest
from _pytest.monkeypatch import MonkeyPatch

from .util.requests_cache import activate_requests_cache

logger = getLogger(__name__)


def pytest_configure(config: Config) -> None:
    config.addinivalue_line(
        "markers", "requests_cache_disabled: Disable caching of requests."
    )
    config.addinivalue_line(
        "markers", "requests_cache_regenerate: Regenerate requested cached requests."
    )


@pytest.fixture(autouse=True)
def cache_requests(request: FixtureRequest, monkeypatch: MonkeyPatch) -> None:
    if request.node.get_closest_marker("requests_cache_disabled"):
        return
    regenerate = bool(request.node.get_closest_marker("requests_cache_regenerate"))
    activate_requests_cache(monkeypatch, regenerate)


@pytest.fixture(autouse=True)
def disrespect_robotstxt() -> None:
    environ["NASTY_DISRESPECT_ROBOTSTXT"] = "1"


@pytest.fixture(autouse=True)
def setup_logging() -> None:
    getLogger(urllib3.__name__).setLevel(INFO)
