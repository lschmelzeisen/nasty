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

from datetime import datetime
from pathlib import Path
from typing import Mapping, Optional, cast

from overrides import overrides
from typing_extensions import Final

from .._util.consts import NASTY_DATE_TIME_FORMAT
from .._util.json_ import JsonSerializable, JsonSerializedException
from .._util.typing_ import checked_cast
from ..request.request import Request

BatchEntryId = str


class BatchEntry(JsonSerializable):
    def __init__(
        self,
        request: Request,
        *,
        id_: BatchEntryId,
        completed_at: Optional[datetime],
        exception: Optional[JsonSerializedException],
    ):
        self.request: Final = request
        self.id: Final = id_
        self.completed_at = completed_at
        self.exception = exception

    def __eq__(self, other: object) -> bool:
        return type(self) == type(other) and self.__dict__ == other.__dict__

    @property
    def meta_file_name(self) -> Path:
        return Path("{:s}.meta.json".format(self.id))

    @property
    def data_file_name(self) -> Path:
        return Path("{:s}.data.jsonl.xz".format(self.id))

    @property
    def ids_file_name(self) -> Path:
        return Path("{:s}.ids".format(self.id))

    @overrides
    def to_json(self) -> Mapping[str, object]:
        obj = {
            "id": self.id,
            "request": self.request.to_json(),
        }
        if self.completed_at:
            obj["completed_at"] = self.completed_at.strftime(NASTY_DATE_TIME_FORMAT)
        if self.exception is not None:
            obj["exception"] = self.exception.to_json()
        return obj

    @classmethod
    @overrides
    def from_json(cls, obj: Mapping[str, object]) -> "BatchEntry":
        return cls(
            request=Request.from_json(cast(Mapping[str, object], obj["request"])),
            id_=checked_cast(str, obj["id"]),
            completed_at=(
                datetime.strptime(
                    checked_cast(str, obj["completed_at"]), NASTY_DATE_TIME_FORMAT
                )
                if "completed_at" in obj
                else None
            ),
            exception=(
                JsonSerializedException.from_json(
                    cast(Mapping[str, object], obj["exception"])
                )
                if "exception" in obj
                else None
            ),
        )
