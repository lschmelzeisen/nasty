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

import pickle
from logging import getLogger
from pathlib import Path
from threading import Lock
from types import TracebackType
from typing import Any, Callable, Dict, Optional, Type

from _pytest.monkeypatch import MonkeyPatch
from requests import PreparedRequest, Response, Session
from typing_extensions import Final

logger = getLogger(__name__)
_SESSION_SEND: Final[Callable[..., Response]] = Session.send


class _CacheKey:
    def __init__(self, request: PreparedRequest):
        if any(request.hooks.values()):
            raise NotImplementedError("Usage of hooks not supported.")

        self._method: Final = request.method
        self._url: Final = request.url
        self._headers: Final = frozenset(request.headers.items())
        self._cookies: Final = frozenset(request._cookies.items())  # type: ignore
        self._body: Final = request.body
        self._body_position: Final = request._body_position  # type: ignore

    def __hash__(self) -> int:
        return hash(frozenset(self.__dict__.items()))

    def __eq__(self, other: object) -> bool:
        return type(self) == type(other) and self.__dict__ == other.__dict__


class RequestsCache:
    def __init__(self) -> None:
        self._lock = Lock()
        self._cache: Dict[_CacheKey, Response] = {}
        self._cache_file = Path(__file__).parent / ".requests_cache.pickle"
        if self._cache_file.exists():
            with self._cache_file.open("rb") as fin:
                self._cache = pickle.load(fin)

    def close(self) -> None:
        with self._cache_file.open("wb") as fout:
            pickle.dump(self._cache, fout, protocol=4)

    def __enter__(self) -> "RequestsCache":
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        self.close()

    def activate(self, monkeypatch: MonkeyPatch, regenerate: bool = False) -> None:
        def mock_session_send(
            session: Session, request: PreparedRequest, **kwargs: Any
        ) -> Response:
            key = _CacheKey(request)
            with self._lock:
                response = self._cache.get(key)
                if response is not None:
                    logger.debug(
                        "Found cache response"
                        + ("." if not regenerate else " (regenerating).")
                    )

                    if not regenerate:
                        session.cookies.update(response.cookies)  # type: ignore
                        return response

                    self._cache.pop(key)

                response = _SESSION_SEND(session, request, **kwargs)
                self._cache[key] = response
                return response

        monkeypatch.setattr(Session, "send", mock_session_send)
