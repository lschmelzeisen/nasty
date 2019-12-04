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

import enum
import json
import lzma
import multiprocessing
from collections import Counter
from datetime import datetime
from enum import Enum
from logging import getLogger
from os import environ
from pathlib import Path
from typing import List, Mapping, Optional, cast
from uuid import uuid4

from overrides import overrides
from typing_extensions import Final

from ._util.consts import NASTY_DATE_TIME_FORMAT
from ._util.json_ import JsonSerializable, JsonSerializedException
from ._util.typing_ import checked_cast
from .request.request import Request

logger = getLogger(__name__)


class _Job(JsonSerializable):
    def __init__(
        self,
        request: Request,
        *,
        id_: str,
        completed_at: Optional[datetime],
        exception: Optional[JsonSerializedException],
    ):
        self.request: Final = request
        self._id: Final = id_
        self.completed_at = completed_at
        self.exception = exception

    @overrides
    def __eq__(self, other: object) -> bool:
        return type(self) == type(other) and self.__dict__ == other.__dict__

    @property
    def meta_file_name(self) -> Path:
        return Path("{:s}.meta.json".format(self._id))

    @property
    def data_file_name(self) -> Path:
        return Path("{:s}.data.jsonl.xz".format(self._id))

    @overrides
    def to_json(self) -> Mapping[str, object]:
        obj = {
            "id": self._id,
            "request": self.request.to_json(),
        }
        if self.completed_at:
            obj["completed_at"] = self.completed_at.strftime(NASTY_DATE_TIME_FORMAT)
        if self.exception is not None:
            obj["exception"] = self.exception.to_json()
        return obj

    @classmethod
    @overrides
    def from_json(cls, obj: Mapping[str, object]) -> "_Job":
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


class _JobResult(Enum):
    SUCCESS = enum.auto()
    SKIP = enum.auto()
    FAIL = enum.auto()


class RequestExecutor:
    def __init__(self) -> None:
        self._jobs: List[_Job] = []

    def submit(self, request: Request) -> None:
        self._jobs.append(
            _Job(request, id_=uuid4().hex, completed_at=None, exception=None)
        )

    def dump_requests(self, file: Path) -> None:
        logger.debug("Saving requests to file '{}'.".format(file))
        with file.open("w", encoding="UTF-8") as fout:
            for job in self._jobs:
                json.dump(job.to_json(), fout)
                fout.write("\n")

    def load_requests(self, file: Path) -> None:
        logger.debug("Loading requests from file '{}'.".format(file))
        with file.open("r", encoding="UTF-8") as fin:
            for line in fin:
                self._jobs.append(_Job.from_json(json.loads(line)))

    def execute(self, out_dir: Path) -> bool:
        logger.debug("Started executing {:d} requests.".format(len(self._jobs)))
        Path.mkdir(out_dir, exist_ok=True, parents=True)

        num_processes = int(environ.get("NASTY_NUM_PROCESSES", "1"))
        with multiprocessing.Pool(processes=num_processes) as pool:
            result_counter = Counter(
                pool.starmap(self._execute_job, ((job, out_dir) for job in self._jobs))
            )

        logger.info(
            "Executing requests completed. "
            "{:d} successful, {:d} skipped, {:d} failed.".format(
                result_counter[_JobResult.SUCCESS],
                result_counter[_JobResult.SKIP],
                result_counter[_JobResult.FAIL],
            )
        )
        if result_counter[_JobResult.FAIL]:
            logger.error("Some requests failed!")
            return False
        return True

    @classmethod
    def _execute_job(cls, job: _Job, out_dir: Path) -> _JobResult:
        logger.debug("Executing request: {}".format(job.request.to_json()))

        meta_file = out_dir / job.meta_file_name
        data_file = out_dir / job.data_file_name

        if meta_file.exists():
            logger.debug("  Loading meta information from previous execution")

            with meta_file.open("r", encoding="UTF-8") as fin:
                previous_job = _Job.from_json(json.load(fin))

            if job.request != previous_job.request:
                logger.error(
                    "  Request from previous execution does not match current one, "
                    "manual intervention required! If the already stored data is "
                    "erroneous, delete the meta and data files of this request and "
                    "rerun the executor."
                )
                logger.error("    Meta file: {}".format(meta_file))
                logger.error("    Data file: {}".format(data_file))
                return _JobResult.FAIL

            if previous_job.completed_at:
                logger.debug(
                    "  Skipping request, because marked as completed at {}.".format(
                        previous_job.completed_at.strftime(NASTY_DATE_TIME_FORMAT)
                    )
                )
                return _JobResult.SKIP

            job = previous_job
            # Don't save previous exceptions back to file
            job.exception = None

        if data_file.exists():
            logger.info(
                "  Deleting previously created data file '{}' because request "
                "execution did not succeed.".format(data_file)
            )
            data_file.unlink()

        result = _JobResult.SUCCESS
        try:
            tweets = list(job.request.request())
            with lzma.open(data_file, "wt", encoding="UTF-8") as fout:
                for tweet in tweets:
                    json.dump(tweet.to_json(), fout)
                    fout.write("\n")

            job.completed_at = datetime.now()
        except Exception as e:
            logger.exception("  Request execution failed with exception.")
            job.exception = JsonSerializedException.from_exception(e)
            result = _JobResult.FAIL

        with meta_file.open("w", encoding="UTF-8") as fout:
            json.dump(job.to_json(), fout, indent=2)

        return result
