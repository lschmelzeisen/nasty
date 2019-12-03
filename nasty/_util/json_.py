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

import traceback
from abc import abstractmethod
from datetime import datetime
from typing import Iterable, Mapping, Type, TypeVar, cast

from overrides import overrides
from typing_extensions import Final

from .consts import NASTY_DATE_TIME_FORMAT
from .typing_ import checked_cast

_T_JsonSerializable = TypeVar("_T_JsonSerializable", bound="JsonSerializable")


class JsonSerializable:
    @abstractmethod
    def to_json(self) -> Mapping[str, object]:
        raise NotImplementedError()

    @classmethod
    @abstractmethod
    def from_json(
        cls: Type[_T_JsonSerializable], obj: Mapping[str, object]
    ) -> _T_JsonSerializable:
        raise NotImplementedError()

    @overrides
    def __repr__(self) -> str:
        return type(self).__name__ + repr(self.to_json())


class JsonSerializedException(JsonSerializable):
    def __init__(
        self, time: datetime, type_: str, message: str, trace: Iterable[Iterable[str]]
    ):
        self.time: Final = time
        self.type: Final = type_
        self.message: Final = message
        self.trace: Final = trace

    @overrides
    def __eq__(self, other: object) -> bool:
        return type(self) == type(other) and self.__dict__ == other.__dict__

    @overrides
    def to_json(self) -> Mapping[str, object]:
        return {
            "time": self.time.strftime(NASTY_DATE_TIME_FORMAT),
            "type": self.type,
            "message": self.message,
            "trace": self.trace,
        }

    @classmethod
    @overrides
    def from_json(cls, obj: Mapping[str, object]) -> "JsonSerializedException":
        return cls(
            time=datetime.strptime(
                checked_cast(str, obj["time"]), NASTY_DATE_TIME_FORMAT
            ),
            type_=checked_cast(str, obj["type"]),
            message=checked_cast(str, obj["message"]),
            trace=cast(Iterable[Iterable[str]], obj["trace"]),
        )

    @classmethod
    def from_exception(cls, exception: Exception) -> "JsonSerializedException":
        type_ = type(exception).__name__
        return cls(
            time=datetime.now(),
            type_=type_,
            message="{}: {}".format(type_, str(exception)),
            # rstrip/split() to be easier to read in formatted JSON.
            trace=[
                frame.rstrip().split("\n")
                for frame in traceback.format_tb(exception.__traceback__)
            ],
        )
