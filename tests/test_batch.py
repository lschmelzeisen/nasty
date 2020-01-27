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
import logging
import lzma
from datetime import date, datetime
from http import HTTPStatus
from pathlib import Path
from typing import Sequence

import pytest
import responses
from _pytest.logging import LogCaptureFixture
from _pytest.monkeypatch import MonkeyPatch

from nasty._util.json_ import JsonSerializedException
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
    # Collect exception with trace.
    try:
        raise ValueError("Test Error.")
    except ValueError as e:
        exception = JsonSerializedException.from_exception(e)

    batch_entry = BatchEntry(
        Search("q"), id_="id", completed_at=None, exception=exception
    )
    assert batch_entry == batch_entry.from_json(batch_entry.to_json())


# -- test_dump_load_requests_* ---------------------------------------------------------


@pytest.mark.parametrize("request_", REQUESTS, ids=repr)
def test_dump_load_single(request_: Request, tmp_path: Path) -> None:
    batch_file = tmp_path / "batch.jsonl"

    batch_executor = Batch()
    batch_executor.append(request_)
    batch_executor.dump(batch_file)

    with batch_file.open("r", encoding="UTF-8") as fin:
        lines = fin.readlines()
    assert 1 == len(lines)
    assert 0 != len(lines[0])

    batch_executor2 = Batch()
    batch_executor2.load(batch_file)
    assert batch_executor.entries == batch_executor2.entries


@pytest.mark.parametrize("num_batch_entries", [10, 505, 1000], ids=repr)
def test_dump_load_multiple(num_batch_entries: int, tmp_path: Path) -> None:
    batch_file = tmp_path / "batch.jsonl"

    batch_executor = Batch()
    for i in range(1, num_batch_entries + 1):
        batch_executor.append(Search(str(i), max_tweets=i, batch_size=i))
    batch_executor.dump(batch_file)

    with batch_file.open("r", encoding="UTF-8") as fin:
        lines = fin.readlines()
    assert num_batch_entries == len(lines)
    for line in lines:
        assert 0 != len(line)

    batch_executor2 = Batch()
    batch_executor2.load(batch_file)
    assert batch_executor.entries == batch_executor2.entries


# -- test_execute_* --------------------------------------------------------------------


def _assert_results_dir_structure(
    results_dir: Path,
    batch_entries: Sequence[BatchEntry],
    caplog: LogCaptureFixture,
    *,
    allow_empty: bool = False,
) -> None:
    assert results_dir.exists()
    assert 0 != len(batch_entries)

    # Check that BatchResults does not log warnings about unknown files in results_dir.
    with caplog.at_level(logging.WARNING):
        caplog.clear()
        batch_results = BatchResults(results_dir)
        assert not caplog.records

    # Can't create sets, because BatchEntry is not hashable, thus compare maps.
    assert {batch_entry._id: batch_entry for batch_entry in batch_entries} == {
        batch_entry._id: batch_entry for batch_entry in batch_results.entries
    }

    for batch_entry in batch_results.entries:
        assert batch_entry.completed_at is not None
        assert datetime.now() > batch_entry.completed_at
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


def test_execute_success(tmp_path: Path, caplog: LogCaptureFixture) -> None:
    batch = Batch()
    batch.append(Search("trump", max_tweets=50))
    batch.append(Search("hillary", max_tweets=50))
    batch.append(Search("obama", max_tweets=50))
    assert batch.execute(tmp_path)
    _assert_results_dir_structure(tmp_path, batch.entries, caplog)


def test_execute_success_parallel(
    tmp_path: Path, monkeypatch: MonkeyPatch, caplog: LogCaptureFixture
) -> None:
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
    _assert_results_dir_structure(tmp_path, batch.entries, caplog)


def test_execute_success_empty(tmp_path: Path, caplog: LogCaptureFixture) -> None:
    # Random string that currently does not match any Tweet.
    unknown_word = "c9dde8b5451149e683d4f07e4c4348ef"
    batch = Batch()
    batch.append(Search(unknown_word))
    assert batch.execute(tmp_path)
    _assert_results_dir_structure(tmp_path, batch.entries, caplog, allow_empty=True)
    with lzma.open(tmp_path / batch.entries[0].data_file_name, "rb") as fin:
        assert 0 == len(fin.read())


def test_execute_previous_match_stray_meta(
    tmp_path: Path, caplog: LogCaptureFixture
) -> None:
    batch = Batch()
    batch.append(Search("trump", max_tweets=50))

    # Create stray (but matching) meta file.
    batch_entry = batch.entries[0]
    meta_file = tmp_path / batch_entry.meta_file_name
    with meta_file.open("w", encoding="UTF-8") as fout:
        json.dump(batch_entry.to_json(), fout, indent=2)
    meta_stat1 = meta_file.stat()

    # Run and verify that this executes the request without problems.
    assert batch.execute(tmp_path)
    _assert_results_dir_structure(tmp_path, batch.entries, caplog)
    meta_stat2 = meta_file.stat()
    assert meta_stat1.st_mtime_ns < meta_stat2.st_mtime_ns


def test_execute_previous_match_stray_data(
    tmp_path: Path, caplog: LogCaptureFixture
) -> None:
    batch = Batch()
    batch.append(Search("trump", max_tweets=50))

    # Create stray data file (with non-matching data).
    batch_entry = batch.entries[0]
    data_file = tmp_path / batch_entry.data_file_name
    with data_file.open("w", encoding="UTF-8") as fout:
        fout.write('INVALID DATA, NOT A JSON "\'""')
    data_stat1 = data_file.stat()

    # Run and verify that this executes the request with problems.
    assert batch.execute(tmp_path)
    _assert_results_dir_structure(tmp_path, batch.entries, caplog)
    data_stat2 = data_file.stat()
    assert data_stat1.st_mtime_ns < data_stat2.st_mtime_ns


def test_execute_previous_match_completed(
    tmp_path: Path, caplog: LogCaptureFixture
) -> None:
    batch_file = tmp_path / "batch.jsonl"
    results_dir = tmp_path / "out"

    # Execute request for the first time.
    batch = Batch()
    batch.append(Search("trump", max_tweets=50))
    batch.dump(batch_file)
    assert batch.execute(results_dir)
    _assert_results_dir_structure(results_dir, batch.entries, caplog)

    batch_entry = batch.entries[0]
    meta_file = results_dir / batch_entry.meta_file_name
    data_file = results_dir / batch_entry.data_file_name
    meta_stat1 = meta_file.stat()
    data_stat1 = data_file.stat()

    # Execute same request again (should be skipped).
    batch = Batch()  # Recreate from dumped batch file so that batch entry IDs match.
    batch.load(batch_file)
    assert batch.execute(results_dir)
    _assert_results_dir_structure(results_dir, batch.entries, caplog)
    meta_stat2 = meta_file.stat()
    data_stat2 = data_file.stat()

    # Verify that files were not modified.
    assert meta_stat1.st_atime_ns <= meta_stat2.st_atime_ns
    assert meta_stat1.st_mtime_ns == meta_stat2.st_mtime_ns
    assert data_stat1.st_atime_ns == data_stat2.st_atime_ns
    assert data_stat1.st_mtime_ns == data_stat2.st_mtime_ns


def test_execute_no_match(tmp_path: Path, caplog: LogCaptureFixture) -> None:
    batch = Batch()
    batch.append(Search("trump", max_tweets=50))

    # Execute successful search request with "trump".
    assert batch.execute(tmp_path)
    _assert_results_dir_structure(tmp_path, batch.entries, caplog)

    # Change request to instead search for "obama".
    meta_file = tmp_path / batch.entries[0].meta_file_name
    with meta_file.open("r", encoding="UTF-8") as fin:
        batch_entry = BatchEntry.from_json(json.load(fin))
    batch.entries[0] = BatchEntry(
        Search("obama"),
        id_=batch_entry._id,
        completed_at=batch_entry.completed_at,
        exception=batch_entry.exception,
    )

    # Verify that this fails because of batch_entry description mismatch.
    assert not batch.execute(tmp_path)

    # Delete offending meta file, run again, and verify that it works now.
    meta_file.unlink()
    assert batch.execute(tmp_path)
    _assert_results_dir_structure(tmp_path, batch.entries, caplog)


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
    batch_entry = batch.entries[0]
    with (tmp_path / batch_entry.meta_file_name).open("r", encoding="UTF-8") as fin:
        batch_entry = BatchEntry.from_json(json.load(fin))
    assert batch_entry.exception is not None
    assert batch_entry.exception.type == "UnexpectedStatusCodeException"
