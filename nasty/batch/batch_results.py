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

from logging import getLogger
from pathlib import Path
from typing import Iterable, Iterator, Optional, Sequence, Union, overload

from .._util.io_ import read_lines_file, write_lines_file
from .._util.json_ import read_json, read_json_lines, write_json, write_jsonl_lines
from .._util.tweepy_ import statuses_lookup
from ..tweet.tweet import Tweet, TweetId
from .batch_entry import BatchEntry

logger = getLogger(__name__)


class BatchResults(Sequence[BatchEntry]):
    def __init__(self, results_dir: Path):
        self._results_dir = results_dir
        self._entries: Sequence[BatchEntry] = [
            read_json(meta_file, BatchEntry)
            for meta_file in self._results_dir.iterdir()
            if meta_file.name.endswith(".meta.json")
        ]

    def tweets(self, entry: BatchEntry) -> Iterable[Tweet]:
        data_file = self._results_dir / entry.data_file_name
        ids_file = self._results_dir / entry.ids_file_name
        if not data_file.exists() and ids_file.exists():
            raise ValueError("Tweet data not available. Did you forget to unidify?")

        yield from read_json_lines(data_file, Tweet, use_lzma=True)

    def tweet_ids(self, entry: BatchEntry) -> Iterable[TweetId]:
        data_file = self._results_dir / entry.data_file_name
        ids_file = self._results_dir / entry.ids_file_name
        if ids_file.exists():
            yield from read_lines_file(ids_file)
        else:
            yield from (
                tweet.id for tweet in read_json_lines(data_file, Tweet, use_lzma=True)
            )

    def idify(self, results_dir: Optional[Path] = None) -> "BatchResults":
        if results_dir is None:
            results_dir = self._results_dir

        logger.debug(
            "Idifying batch results from '{}' to "
            "'{}'.".format(self._results_dir, results_dir)
        )

        same_dir = results_dir.exists() and results_dir.samefile(self._results_dir)
        if not same_dir:
            Path.mkdir(results_dir, exist_ok=True, parents=True)

        for entry in self._entries:
            ids_file = results_dir / entry.ids_file_name
            meta_file = results_dir / entry.meta_file_name

            if not ids_file.exists():
                write_lines_file(ids_file, self.tweet_ids(entry))

            if not meta_file.exists():
                write_json(meta_file, entry)

        if not same_dir:
            return BatchResults(results_dir)
        return self

    def unidify(self, results_dir: Optional[Path] = None) -> "BatchResults":
        if results_dir is None:
            results_dir = self._results_dir

        logger.debug(
            "Unidifying batch results from '{}' to "
            "'{}'.".format(self._results_dir, results_dir)
        )

        same_dir = results_dir.exists() and results_dir.samefile(self._results_dir)
        if not same_dir:
            Path.mkdir(results_dir, exist_ok=True, parents=True)

        for entry in self._entries:
            data_file = results_dir / entry.data_file_name
            meta_file = results_dir / entry.meta_file_name

            if not data_file.exists():
                write_jsonl_lines(
                    data_file,
                    (
                        tweet
                        for tweet in statuses_lookup(self.tweet_ids(entry))
                        if tweet is not None
                    ),
                    use_lzma=True,
                )

            if not meta_file.exists():
                write_json(meta_file, entry)

        if not same_dir:
            return BatchResults(results_dir)
        return self

    def __len__(self) -> int:
        return len(self._entries)

    def __contains__(self, item: object) -> bool:
        return item in self._entries

    @overload
    def __getitem__(self, _index: int) -> BatchEntry:
        ...

    @overload  # noqa: F811
    def __getitem__(self, _slice: slice) -> Sequence[BatchEntry]:
        ...

    def __getitem__(  # noqa: F811
        self, index_or_slice: Union[int, slice]
    ) -> Union[BatchEntry, Sequence[BatchEntry]]:
        return self._entries[index_or_slice]

    def __iter__(self) -> Iterator[BatchEntry]:
        return iter(self._entries)

    def __repr__(self) -> str:
        return repr(self._entries)
