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

import json
import lzma
from logging import getLogger
from pathlib import Path
from typing import Iterable, Optional, Sequence

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
            ids_file = self._results_dir / (id_ + ".ids")
            if not (data_file.exists() or ids_file.exists()):
                logger.error(
                    "Tweet result files missing (i.e., no data or Tweet-IDs file) "
                    "for meta file '{}' in batch result dir "
                    "'{}'.".format(meta_file.name, self._results_dir)
                )
            known_files.add(meta_file)
            known_files.add(data_file)
            known_files.add(ids_file)

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
        if not data_file.exists():
            error = "Can not load Tweets, as data file '{}' does not exist.".format(
                data_file.name
            )

            ids_file = self._results_dir / entry.ids_file_name
            if ids_file.exists():
                error += (
                    " However, could find Tweet-IDs file '{}'. Did you forget to "
                    "unidify?".format(ids_file.name)
                )

            raise ValueError(error)

        with lzma.open(data_file, "rt", encoding="UTF-8") as fin:
            for line in fin:
                yield Tweet.from_json(json.loads(line))

    def idify(self, results_dir: Optional[Path] = None) -> "BatchResults":
        if results_dir is None:
            results_dir = self._results_dir

        logger.debug(
            "Idifying batch results from '{}' to "
            "'{}'".format(self._results_dir, results_dir)
        )

        same_dir = results_dir.exists() and results_dir.samefile(self._results_dir)
        if not same_dir:
            Path.mkdir(results_dir, exist_ok=True, parents=True)

        for entry in self.entries:
            meta_file = results_dir / entry.meta_file_name
            ids_file = results_dir / entry.ids_file_name

            if meta_file.exists() and ids_file.exists():
                with meta_file.open("r", encoding="UTF-8") as fin:
                    prev_execution_entry = BatchEntry.from_json(json.load(fin))

                if entry != prev_execution_entry:
                    raise ValueError(
                        "Found meta information from previous execution that does not "
                        "match current one, manual intervention required! If the "
                        "already stored data is erroneous, delete the files of this ID "
                        "and restart idification. Meta file: '{}'.".format(meta_file)
                    )

                logger.debug(
                    "  Skipping entry '{}', as matching meta file and Tweet-IDs file "
                    "already exist.".format(entry._id)
                )
                continue

            with ids_file.open("w", encoding="UTF-8") as fout:
                for tweet in self.tweets(entry):
                    fout.write("{}\n".format(tweet.id))

            if not same_dir:
                with meta_file.open("w", encoding="UTF-8") as fout:
                    json.dump(entry.to_json(), fout, indent=2)

        if not same_dir:
            return BatchResults(results_dir)
        return self
