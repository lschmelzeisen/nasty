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
from datetime import date, datetime
from http import HTTPStatus
from pathlib import Path
from typing import Sequence

import pytest
import responses
from _pytest.logging import LogCaptureFixture
from _pytest.monkeypatch import MonkeyPatch

from nasty._util.io_ import read_file, read_lines_file, write_file
from nasty._util.json_ import JsonSerializedException, read_json, write_json
from nasty._util.typing_ import checked_cast
from nasty.batch.batch import Batch
from nasty.batch.batch_entry import BatchEntry
from nasty.batch.batch_results import BatchResults
from nasty.request.replies import Replies
from nasty.request.request import Request
from nasty.request.search import Search, SearchFilter
from nasty.request.thread import Thread

REQUESTS: Sequence[Request] = [
    Search("q"),
    Search("q", filter_=SearchFilter.PHOTOS, lang="de"),
    Search("q", since=date(2009, 1, 20), until=date(2017, 1, 20)),
    Replies("332308211321425920"),
    Replies("332308211321425920", max_tweets=50),
    Thread("332308211321425920"),
    Thread("332308211321425920", batch_size=100),
]


def _make_json_serialized_exception() -> JsonSerializedException:
    # Collect exception with trace.
    try:
        raise ValueError("Test Error.")
    except ValueError as e:
        return JsonSerializedException.from_exception(e)


# -- test_json_conversion_* ------------------------------------------------------------


@pytest.mark.parametrize("request_", REQUESTS, ids=repr)
def test_json_conversion_request(request_: Request) -> None:
    batch_entry = BatchEntry(request_, id_="id", completed_at=None, exception=None)
    assert batch_entry == batch_entry.from_json(batch_entry.to_json())


def test_json_conversion_completed_at() -> None:
    batch_entry = BatchEntry(
        Search("q"), id_="id", completed_at=datetime.now(), exception=None
    )
    assert batch_entry == batch_entry.from_json(batch_entry.to_json())


def test_json_conversion_exception() -> None:
    batch_entry = BatchEntry(
        Search("q"),
        id_="id",
        completed_at=None,
        exception=_make_json_serialized_exception(),
    )
    assert batch_entry == batch_entry.from_json(batch_entry.to_json())


# -- test_dump_load_requests_* ---------------------------------------------------------


@pytest.mark.parametrize("request_", REQUESTS, ids=repr)
def test_dump_load_single(request_: Request, tmp_path: Path) -> None:
    batch_file = tmp_path / "batch.jsonl"

    batch = Batch()
    batch.append(request_)
    batch.dump(batch_file)

    lines = list(read_lines_file(batch_file))
    assert 1 == len(lines)
    assert 0 != len(lines[0])

    batch2 = Batch()
    batch2.load(batch_file)
    assert list(batch) == list(batch2)


@pytest.mark.parametrize("num_batch_entries", [10, 505, 1000], ids=repr)
def test_dump_load_multiple(num_batch_entries: int, tmp_path: Path) -> None:
    batch_file = tmp_path / "batch.jsonl"

    batch = Batch()
    for i in range(1, num_batch_entries + 1):
        batch.append(Search(str(i), max_tweets=i, batch_size=i))
    batch.dump(batch_file)

    lines = list(read_lines_file(batch_file))
    assert num_batch_entries == len(lines)
    for line in lines:
        assert 0 != len(line)

    batch2 = Batch()
    batch2.load(batch_file)
    assert list(batch) == list(batch2)


# -- test_execute_* --------------------------------------------------------------------


def _assert_results_dir_structure(
    results_dir: Path,
    batch_entries: Sequence[BatchEntry],
    *,
    allow_empty: bool = False,
) -> None:
    assert results_dir.exists()
    assert 0 != len(batch_entries)

    batch_results = BatchResults(results_dir)

    # Can't create sets, because BatchEntry is not hashable, thus compare maps.
    assert {batch_entry.id: batch_entry for batch_entry in batch_entries} == {
        batch_entry.id: batch_entry for batch_entry in batch_results
    }

    for batch_entry in batch_results:
        assert batch_entry.completed_at is not None
        assert batch_entry.completed_at < datetime.now()
        assert batch_entry.exception is None

        tweets = list(batch_results.tweets(batch_entry))
        if not allow_empty:
            assert 0 != len(tweets)

        assert checked_cast(int, batch_entry.request.max_tweets) >= len(tweets)
        for tweet in tweets:
            assert (
                checked_cast(Search, batch_entry.request).query.lower()
                in json.dumps(tweet.to_json()).lower()
            )


def test_execute_success(tmp_path: Path) -> None:
    batch = Batch()
    batch.append(Search("trump", max_tweets=50))
    batch.append(Search("hillary", max_tweets=50))
    batch.append(Search("obama", max_tweets=50))
    assert batch.execute(tmp_path)
    _assert_results_dir_structure(tmp_path, list(batch))


def test_execute_success_parallel(tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("NASTY_NUM_WORKERS", "4")
    batch = Batch()
    for i in range(16):
        batch.append(
            Search(
                "trump",
                since=date(2019, 1, i + 1),
                until=date(2019, 1, i + 2),
                max_tweets=50,
            )
        )
    assert batch.execute(tmp_path)
    _assert_results_dir_structure(tmp_path, list(batch))


def test_execute_success_empty(tmp_path: Path) -> None:
    # Random string that currently does not match any Tweet.
    unknown_word = "c9dde8b5451149e683d4f07e4c4348ef"
    batch = Batch()
    batch.append(Search(unknown_word))
    results = batch.execute(tmp_path)
    assert results
    assert not list(results.tweets(results[0]))
    _assert_results_dir_structure(tmp_path, list(batch), allow_empty=True)


def test_execute_retrying_after_exception(
    tmp_path: Path, caplog: LogCaptureFixture
) -> None:
    batch = Batch()
    batch.append(Search("trump", max_tweets=50))

    batch_entry = batch[0]
    exception = _make_json_serialized_exception()
    batch_entry.exception = exception
    meta_file = tmp_path / batch_entry.meta_file_name
    write_json(meta_file, batch_entry)
    batch_entry.exception = None
    meta_stat1 = meta_file.stat()

    caplog.clear()
    assert batch.execute(tmp_path)
    assert 1 == len(  # Assert that log says we are retrying and the previous exception.
        [
            record
            for record in caplog.records
            if "Retrying" in record.msg and str(exception) in record.msg
        ]
    )

    _assert_results_dir_structure(tmp_path, list(batch))
    meta_stat2 = meta_file.stat()
    assert meta_stat1.st_mtime_ns < meta_stat2.st_mtime_ns


def test_execute_stray_data_file(tmp_path: Path, caplog: LogCaptureFixture) -> None:
    batch = Batch()
    batch.append(Search("trump", max_tweets=50))

    batch_entry = batch[0]
    data = "Just some stray data."
    data_file = tmp_path / batch_entry.data_file_name
    write_file(data_file, data)
    data_stat1 = data_file.stat()

    assert not batch.execute(tmp_path)

    # Assert exception is saved.
    assert batch_entry == read_json(tmp_path / batch_entry.meta_file_name, BatchEntry)
    assert batch_entry.exception is not None
    assert batch_entry.exception.type == "ValueError"
    batch_entry.exception = None

    # Assert that previous data file is not modified.
    data_stat2 = data_file.stat()
    assert data_stat1.st_mtime == data_stat2.st_mtime
    assert data == read_file(data_file)

    # Delete data file and verify that it works now.
    data_file.unlink()
    caplog.clear()
    assert batch.execute(tmp_path)
    assert 1 == len([record for record in caplog.records if "Retrying" in record.msg])
    _assert_results_dir_structure(tmp_path, list(batch))


def test_execute_skipping(tmp_path: Path, caplog: LogCaptureFixture) -> None:
    batch_file = tmp_path / "batch.jsonl"
    results_dir = tmp_path / "out"

    # Execute request for the first time.
    batch = Batch()
    batch.append(Search("trump", max_tweets=50))
    batch.dump(batch_file)
    assert batch.execute(results_dir)
    _assert_results_dir_structure(results_dir, list(batch))

    batch_entry = batch[0]
    meta_file = results_dir / batch_entry.meta_file_name
    data_file = results_dir / batch_entry.data_file_name
    meta_stat1 = meta_file.stat()
    data_stat1 = data_file.stat()

    # Execute same request again (should be skipped).
    batch = Batch()  # Recreate from dumped batch file so that batch entry IDs match.
    batch.load(batch_file)
    caplog.clear()
    assert batch.execute(results_dir)
    assert 1 == len([record for record in caplog.records if "Skipping" in record.msg])
    _assert_results_dir_structure(results_dir, list(batch))
    meta_stat2 = meta_file.stat()
    data_stat2 = data_file.stat()

    # Verify that files were not modified.
    assert meta_stat1.st_mtime_ns == meta_stat2.st_mtime_ns
    assert data_stat1.st_mtime_ns == data_stat2.st_mtime_ns


@pytest.mark.requests_cache_disabled
@responses.activate
def test_execute_exception_internal_server_error(tmp_path: Path) -> None:
    # Simulate 500 Internal Server Error on first request to Twitter.
    responses.add(
        responses.GET, "https://mobile.twitter.com/robots.txt", body="Crawl-delay: 1",
    )
    responses.add(
        responses.GET,
        "https://mobile.twitter.com/search",
        match_querystring=False,
        status=HTTPStatus.INTERNAL_SERVER_ERROR.value,
    )

    batch = Batch()
    batch.append(Search("trump", max_tweets=50))
    assert not batch.execute(tmp_path)
    batch_entry = batch[0]
    assert batch_entry == read_json(tmp_path / batch_entry.meta_file_name, BatchEntry)
    assert batch_entry.exception is not None
    assert batch_entry.exception.type == "UnexpectedStatusCodeException"
