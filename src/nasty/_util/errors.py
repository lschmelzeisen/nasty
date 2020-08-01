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

from typing_extensions import Final


class UnexpectedStatusCodeException(Exception):
    def __init__(
        self,
        url: str,
        status_code: HTTPStatus,
        *,
        expected_status_code: HTTPStatus = HTTPStatus.OK,
    ):
        self.url: Final = url
        self.status_code: Final = status_code
        self.expected_status_code: Final = expected_status_code

        super().__init__(
            "Received status code {:d} {:s} (expected {:d} {:s}) for URL "
            '"{:s}".'.format(
                self.status_code.value,
                self.status_code.name,
                self.expected_status_code.value,
                self.expected_status_code.name,
                self.url,
            )
        )
