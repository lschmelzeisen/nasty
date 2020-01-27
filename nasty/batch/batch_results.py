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

import json
import lzma
from logging import getLogger
from pathlib import Path
from typing import Iterable, Sequence

from ..tweet.tweet import Tweet
from .batch_entry import BatchEntry

logger = getLogger(__name__)


class BatchResults:
    def __init__(self, results_dir: Path):
        self._results_dir = results_dir

        files = set(self._results_dir.iterdir())
        known_files = set()
        entries = []
        for meta_file in files:
            if not meta_file.name.endswith(".meta.json"):
                continue

            id_ = meta_file.name[: -len(".meta.json")]
            data_file = self._results_dir / (id_ + ".data.jsonl.xz")
            if not data_file.exists():
                logger.error(
                    "Accompanying data file missing for meta file "
                    "'{}' in batch result dir '{}'.".format(
                        meta_file.name, self._results_dir
                    )
                )
            known_files.add(meta_file)
            known_files.add(data_file)

            with meta_file.open("r", encoding="UTF-8") as fin:
                entries.append(BatchEntry.from_json(json.load(fin)))

        unknown_files = files - known_files
        if unknown_files:
            logger.warning(
                "Unknown files '{}' in batch result dir '{}'.".format(
                    "', '".join(file.name for file in unknown_files), self._results_dir
                )
            )

        self.entries: Sequence[BatchEntry] = entries

    def tweets(self, entry: BatchEntry) -> Iterable[Tweet]:
        data_file = self._results_dir / entry.data_file_name
        with lzma.open(data_file, "rt", encoding="UTF-8") as fin:
            for line in fin:
                yield Tweet.from_json(json.loads(line))
