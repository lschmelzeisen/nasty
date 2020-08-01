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
from operator import itemgetter
from pathlib import Path
from typing import (
    Callable,
    Counter,
    Iterable,
    Iterator,
    Optional,
    Sequence,
    Tuple,
    Union,
    cast,
    overload,
)

from more_itertools import groupby_transform, spy, unzip

from .._util.io_ import read_lines_file, write_lines_file
from .._util.json_ import read_json, read_json_lines, write_json, write_jsonl_lines
from .._util.tweepy_ import statuses_lookup
from ..tweet.tweet import Tweet, TweetId
from ._execute_result import _ExecuteResult
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

    def _transform(
        self,
        new_results_dir: Optional[Path],
        transform_name: str,
        transform_func: Callable[[Path], Counter[_ExecuteResult]],
    ) -> Optional["BatchResults"]:
        results_dir = self._results_dir
        if new_results_dir is not None:
            results_dir = new_results_dir

        logger.debug(
            "{} batch results from '{}' to '{}'.".format(
                transform_name, self._results_dir, results_dir
            )
        )

        same_dir = results_dir.exists() and results_dir.samefile(self._results_dir)
        if not same_dir:
            Path.mkdir(results_dir, exist_ok=True, parents=True)

        result_counter = transform_func(results_dir)
        logger.info(
            "  {} batch results completed. {:d} successful, {:d} skipped, {:d} "
            "failed.".format(
                transform_name,
                result_counter[_ExecuteResult.SUCCESS],
                result_counter[_ExecuteResult.SKIP],
                result_counter[_ExecuteResult.FAIL],
            )
        )

        if result_counter[_ExecuteResult.FAIL]:
            logger.error("  {} failed .".format(transform_name))
            return None
        if not same_dir:
            return BatchResults(results_dir)
        return self

    def idify(self, new_results_dir: Optional[Path] = None) -> Optional["BatchResults"]:
        return self._transform(new_results_dir, "Idifying", self._transform_idify)

    def _transform_idify(self, results_dir: Path) -> Counter[_ExecuteResult]:
        result_counter = Counter[_ExecuteResult]()
        for entry in self:
            try:
                ids_file = results_dir / entry.ids_file_name
                meta_file = results_dir / entry.meta_file_name

                if ids_file.exists() and meta_file.exists():
                    result_counter[_ExecuteResult.SKIP] += 1
                    continue

                write_lines_file(ids_file, self.tweet_ids(entry))
                write_json(meta_file, entry, overwrite_existing=True)
                result_counter[_ExecuteResult.SUCCESS] += 1
            except Exception:
                logger.exception("  Entry '{}' failed with exception.".format(entry.id))
                result_counter[_ExecuteResult.FAIL] += 1
        return result_counter

    def unidify(
        self, new_results_dir: Optional[Path] = None
    ) -> Optional["BatchResults"]:
        return self._transform(new_results_dir, "Unidifying", self._transform_unidify)

    def _transform_unidify(self, results_dir: Path) -> Counter[_ExecuteResult]:
        result_counter = Counter[_ExecuteResult]()

        head, entries_tweet_ids = spy(
            self._iter_entries_tweet_ids(results_dir, result_counter)
        )
        if not head:  # Check if any entries with Tweet-IDs exist (else unzip fails).
            return result_counter

        entries, tweet_ids = cast(
            Tuple[Iterator[BatchEntry], Iterator[TweetId]], unzip(entries_tweet_ids)
        )
        for entry, tweets in groupby_transform(
            zip(entries, statuses_lookup(tweet_ids)),
            keyfunc=itemgetter(0),
            valuefunc=itemgetter(1),
        ):
            write_jsonl_lines(
                results_dir / entry.data_file_name,
                (tweet for tweet in tweets if tweet is not None),
                use_lzma=True,
            )
            write_json(
                results_dir / entry.meta_file_name, entry, overwrite_existing=True
            )
            result_counter[_ExecuteResult.SUCCESS] += 1

        return result_counter

    def _iter_entries_tweet_ids(
        self, results_dir: Path, result_counter: Counter[_ExecuteResult]
    ) -> Iterable[Tuple[BatchEntry, TweetId]]:
        for entry in self:
            meta_file = results_dir / entry.meta_file_name
            data_file = results_dir / entry.data_file_name
            if data_file.exists() and meta_file.exists():
                result_counter[_ExecuteResult.SKIP] += 1
                continue

            is_entry_empty = True
            for tweet in self.tweet_ids(entry):
                is_entry_empty = False
                yield entry, tweet

            if is_entry_empty:
                write_jsonl_lines(results_dir / entry.data_file_name, [], use_lzma=True)
                write_json(
                    results_dir / entry.meta_file_name, entry, overwrite_existing=True
                )
                result_counter[_ExecuteResult.SUCCESS] += 1

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
