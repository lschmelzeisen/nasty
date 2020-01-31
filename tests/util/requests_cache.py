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

import base64
import json
from datetime import timedelta
from http.cookiejar import Cookie, DefaultCookiePolicy
from logging import getLogger
from pathlib import Path
from threading import Lock
from types import TracebackType
from typing import (
    Any,
    Callable,
    Dict,
    Generic,
    Mapping,
    Optional,
    Sequence,
    Tuple,
    Type,
    TypeVar,
    cast,
)

from _pytest.monkeypatch import MonkeyPatch
from requests import PreparedRequest, Response, Session
from requests.cookies import RequestsCookieJar
from requests.hooks import default_hooks
from requests.structures import CaseInsensitiveDict
from typing_extensions import Final

logger = getLogger(__name__)
_SESSION_SEND: Final[Callable[..., Response]] = Session.send
_T_Serializable = TypeVar("_T_Serializable")


class Serializable(Generic[_T_Serializable]):
    def __init__(
        self,
        type_: Type[_T_Serializable],
        encoder: Callable[[_T_Serializable], Dict[str, object]],
        decoder: Optional[Callable[[Dict[str, object]], Dict[str, object]]] = None,
    ):
        self.type = type_
        self.encoder = encoder
        self.decoder = decoder


SERIALIZABLES: Mapping[str, Serializable[Any]] = {
    bytes.__name__: Serializable(
        type_=bytes,
        encoder=lambda obj: {"base64": base64.encodebytes(obj).decode("ascii")},
    ),
    timedelta.__name__: Serializable(
        type_=timedelta,
        encoder=lambda obj: {
            "days": obj.days,
            "seconds": obj.seconds,
            "microseconds": obj.microseconds,
        },
    ),
    CaseInsensitiveDict.__name__: Serializable(
        type_=CaseInsensitiveDict,
        encoder=lambda obj: cast(Dict[str, object], obj._store),
        decoder=lambda obj: {"_store": obj},
    ),
    Cookie.__name__: Serializable(
        type_=Cookie,
        encoder=lambda obj: cast(Dict[str, object], obj.__dict__),
        decoder=lambda obj: obj,
    ),
    RequestsCookieJar.__name__: Serializable(
        type_=RequestsCookieJar,
        encoder=lambda obj: dict(obj.__getstate__(), _policy=None),
        decoder=lambda obj: dict(obj, _policy=DefaultCookiePolicy()),
    ),
    PreparedRequest.__name__: Serializable(
        type_=PreparedRequest,
        encoder=lambda obj: dict(obj.__dict__, hooks=None),
        decoder=lambda obj: dict(
            obj, hooks=cast(Callable[[], Mapping[str, Sequence[Any]]], default_hooks)()
        ),
    ),
    Response.__name__: Serializable(
        type_=Response,
        encoder=lambda obj: dict(obj.__getstate__(), history=None),
        decoder=lambda obj: dict(obj, history=None),
    ),
}


def encode_json(obj: object) -> object:
    try:
        result = SERIALIZABLES[type(obj).__name__].encoder(obj)
    except KeyError:
        return obj
    result["__type__"] = type(obj).__name__
    return result


def decode_json(obj: Dict[str, object]) -> object:
    if not isinstance(obj, Dict) or "__type__" not in obj:
        return obj

    serializable = SERIALIZABLES[cast(str, obj.pop("__type__"))]
    if serializable.decoder is not None:
        result_dict = serializable.decoder(obj)
        result = object.__new__(serializable.type)
        if hasattr(result, "__setstate__"):
            result.__setstate__(result_dict)
        else:
            result.__dict__ = result_dict
        return result
    elif serializable.type == bytes:
        return base64.decodebytes(cast(str, obj["base64"]).encode("ascii"))
    elif serializable.type == timedelta:
        return timedelta(
            days=cast(float, obj["days"]),
            seconds=cast(float, obj["seconds"]),
            microseconds=cast(float, obj["microseconds"]),
        )
    raise ValueError(
        "Decoding type {} not implemented.".format(serializable.type.__name__)
    )


def _request_to_cache_key(request: PreparedRequest) -> Tuple[Any, ...]:
    return (
        request.method,
        request.url,
        tuple(request.headers.items()),
        tuple(request._cookies.items()),  # type: ignore
        request.body,
        request._body_position,  # type: ignore
    )


class RequestsCache:
    def __init__(self) -> None:
        self._lock = Lock()
        self._cache: Dict[Tuple[Any, ...], Response] = {}
        self._cache_file = Path(__file__).parent / ".requests_cache.jsonl"
        if self._cache_file.exists():
            with self._cache_file.open("rt", encoding="UTF-8") as fin:
                for line in fin:
                    response = json.loads(line, object_hook=decode_json)
                    self._cache[_request_to_cache_key(response.request)] = response

    def close(self) -> None:
        with self._cache_file.open("wt", encoding="UTF-8") as fout:
            for response in self._cache.values():
                fout.write(json.dumps(response, default=encode_json))
                fout.write("\n")

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
            with self._lock:
                key = _request_to_cache_key(request)
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

        monkeypatch.setattr(Session, Session.send.__name__, mock_session_send)
