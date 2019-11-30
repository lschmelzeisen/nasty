import traceback
from abc import abstractmethod
from datetime import datetime
from enum import Enum
from typing import Iterable, Mapping, Type, TypeVar, cast

from overrides import overrides
from typing_extensions import Final, final

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


_T_JsonSerializableEnum = TypeVar(
    "_T_JsonSerializableEnum", bound="JsonSerializableEnum"
)


class JsonSerializableEnum(JsonSerializable, Enum):
    @final
    @overrides
    def to_json(self) -> Mapping[str, object]:
        return {"enum": self.name}

    @classmethod
    @final
    @overrides
    def from_json(
        cls: Type[_T_JsonSerializableEnum], obj: Mapping[str, object]
    ) -> _T_JsonSerializableEnum:
        return cls[checked_cast(str, obj["enum"])]


class JsonSerializedException(JsonSerializable):
    def __init__(
        self, time: datetime, type_: str, message: str, trace: Iterable[Iterable[str]]
    ):
        self.time: Final = time
        self.type: Final = type_
        self.message: Final = message
        self.trace: Final = trace

    @overrides
    def __repr__(self) -> str:
        return type(self).__name__ + repr(self.to_json())

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
