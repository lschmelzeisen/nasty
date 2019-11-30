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

import pytest

from nasty.request.replies import Replies
from nasty.request.request import Request
from nasty.request.search import Search
from nasty.request.thread import Thread


@pytest.mark.parametrize(
    "req",
    [
        Search("Trump"),
        Replies("332308211321425920", max_tweets=None),
        Thread("332308211321425920", max_tweets=123, batch_size=456),
    ],
    ids=repr,
)
def test_json_conversion(req: Request) -> None:
    assert req == req.from_json(req.to_json())
