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

from typing import Iterable, Optional

class binder: ...  # noqa: N801

class parsers:  # noqa: N801
    class JSONParser:
        def __init__(self) -> None: ...

class auth:  # noqa: N801
    class AuthHandler: ...

class OAuthHandler(auth.AuthHandler):
    def __init__(self, consumer_key: str, consumer_secret: str): ...
    def set_access_token(self, key: str, secret: str) -> None: ...

class AppAuthHandler(auth.AuthHandler):
    def __init__(self, consumer_key: str, consumer_secret: str): ...

class API:
    def __init__(
        self,
        auth_handler: Optional[auth.AuthHandler] = ...,
        parser: Optional[parsers.JSONParser] = ...,
    ): ...
    def statuses_lookup(
        self,
        id_: Iterable[str],
        include_entities: bool = ...,
        trim_user: bool = ...,
        map_: bool = ...,
        tweet_mode: str = ...,
    ) -> object: ...

class TweepyError(Exception): ...
class RateLimitError(TweepyError): ...
