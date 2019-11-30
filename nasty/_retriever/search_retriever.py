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

from overrides import overrides

from .._util.typing_ import checked_cast
from ..request.search import Search
from .retriever import Retriever


class SearchRetriever(Retriever):
    def __init__(self, request: Search):
        super().__init__(request)

    @property  # type: ignore  # see https://github.com/python/mypy/issues/1362
    @overrides
    def request(self) -> Search:
        return checked_cast(Search, self._request)
