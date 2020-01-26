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
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from enum import Enum
from logging import getLogger
from os import getenv
from pathlib import Path
from typing import List
from uuid import uuid4

from .._util.consts import NASTY_DATE_TIME_FORMAT
from .._util.json_ import JsonSerializedException
from ..request.request import Request
from .batch_entry import BatchEntry

logger = getLogger(__name__)


class _ExecuteResult(Enum):
    SUCCESS = enum.auto()
    SKIP = enum.auto()
    FAIL = enum.auto()


class BatchExecutor:
    def __init__(self) -> None:
        self.entries: List[BatchEntry] = []

    def submit(self, request: Request) -> None:
        self.entries.append(
            BatchEntry(request, id_=uuid4().hex, completed_at=None, exception=None)
        )

    def dump_batch(self, file: Path) -> None:
        logger.debug("Dumping batch to file '{}'.".format(file))
        with file.open("w", encoding="UTF-8") as fout:
            for entry in self.entries:
                json.dump(entry.to_json(), fout)
                fout.write("\n")

    def load_batch(self, file: Path) -> None:
        logger.debug("Loading batch from file '{}'.".format(file))
        with file.open("r", encoding="UTF-8") as fin:
            for line in fin:
                self.entries.append(BatchEntry.from_json(json.loads(line)))

    def execute(self, out_dir: Path) -> bool:
        logger.debug(
            "Started executing batch of {:d} requests.".format(len(self.entries))
        )
        Path.mkdir(out_dir, exist_ok=True, parents=True)

        num_workers = int(getenv("NASTY_NUM_WORKERS", default="1"))
        with ThreadPoolExecutor(max_workers=num_workers) as pool:
            result_counter = Counter(
                future.result()
                for future in as_completed(
                    pool.submit(self._execute_entry, entry, out_dir)
                    for entry in self.entries
                )
            )

        logger.info(
            "Executing batch completed. "
            "{:d} successful, {:d} skipped, {:d} failed.".format(
                result_counter[_ExecuteResult.SUCCESS],
                result_counter[_ExecuteResult.SKIP],
                result_counter[_ExecuteResult.FAIL],
            )
        )
        if result_counter[_ExecuteResult.FAIL]:
            logger.error("Some requests failed!")
            return False
        return True

    @classmethod
    def _execute_entry(cls, entry: BatchEntry, out_dir: Path) -> _ExecuteResult:
        logger.debug("Executing request: {}".format(entry.request.to_json()))

        meta_file = out_dir / entry.meta_file_name
        data_file = out_dir / entry.data_file_name

        if meta_file.exists():
            logger.debug("  Loading meta information from previous batch execution.")

            with meta_file.open("r", encoding="UTF-8") as fin:
                prev_execution_entry = BatchEntry.from_json(json.load(fin))

            if entry.request != prev_execution_entry.request:
                logger.error(
                    "  Request from previous batch execution does not match current "
                    "one, manual intervention required! If the already stored data is "
                    "erroneous, delete the meta and data files of this request and "
                    "restart batch execution."
                )
                logger.error("    Meta file: {}".format(meta_file))
                logger.error("    Data file: {}".format(data_file))
                return _ExecuteResult.FAIL

            if prev_execution_entry.completed_at:
                logger.debug(
                    "  Skipping request, because marked as completed at {}.".format(
                        prev_execution_entry.completed_at.strftime(
                            NASTY_DATE_TIME_FORMAT
                        )
                    )
                )
                return _ExecuteResult.SKIP

            entry = prev_execution_entry
            # Don't save previous execution's exception back to file
            entry.exception = None

        if data_file.exists():
            logger.info(
                "  Deleting previously created data file '{}' because request "
                "execution did not succeed.".format(data_file)
            )
            data_file.unlink()

        result = _ExecuteResult.SUCCESS
        try:
            tweets = list(entry.request.request())
            with lzma.open(data_file, "wt", encoding="UTF-8") as fout:
                for tweet in tweets:
                    json.dump(tweet.to_json(), fout)
                    fout.write("\n")

            entry.completed_at = datetime.now()
        except Exception as e:
            logger.exception("  Request execution failed with exception.")
            entry.exception = JsonSerializedException.from_exception(e)
            result = _ExecuteResult.FAIL

        with meta_file.open("w", encoding="UTF-8") as fout:
            json.dump(entry.to_json(), fout, indent=2)

        return result
