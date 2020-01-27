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

from typing import Any, Iterable

class Retry:
    def __init__(
        self,
        total: int = ...,
        connect: int = ...,
        read: int = ...,
        redirect: int = ...,
        status: int = ...,
        method_whitelist: Iterable[str] = ...,
        status_forcelist: Iterable[int] = ...,
        backoff_factor: float = ...,
        raise_on_redirect: bool = ...,
        raise_on_status: bool = ...,
        history: Any = ...,
        respect_retry_after_header: bool = ...,
        remove_headers_on_redirect: Iterable[Any] = ...,
    ): ...
