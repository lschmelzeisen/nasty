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

from pathlib import Path

import pytest

from nasty.batch.batch import Batch
from nasty.batch.batch_results import BatchResults
from nasty.request.thread import Thread
from nasty.tweet.tweet import TweetId


def _make_batch_results() -> BatchResults:
    batch = Batch()
    batch.append(Thread("1115689254271819777"))
    results = batch.execute()
    assert results is not None
    return results


def _assert_tweet_texts(results: BatchResults) -> None:
    assert [
        "We encourage submissions of new, previously, or concurrently published "
        "research. The event should be a forum for researchers to exchange ideas, "
        "discuss work, and get feedback. We hope you'll consider submitting your work.",
        "We'll have talks from research leaders on the latest advances in NLP. "
        "@NandoDF will be giving the keynote and more speakers will be announced soon. "
        "https://t.co/SB3URxn6ab",
        "Registration will open soon. In the meantime, we'll hope you'll save the date "
        "and consider joining us for what should be a fun day of listening to "
        "stimulating talks, mingling with like-minded people, exchanging ideas, and "
        "maybe even striking up a collaboration.",
    ] == [tweet.text for tweet in results.tweets(results.entries[0])]


def _assert_tweet_ids(results: BatchResults) -> None:
    assert [
        TweetId("1115690002233556993"),
        TweetId("1115690615612825601"),
        TweetId("1115691710657499137"),
    ] == list(results.tweet_ids(results.entries[0]))


def test_tweets_from_exectue() -> None:
    results = _make_batch_results()
    _assert_tweet_texts(results)
    _assert_tweet_ids(results)


def test_tweets_from_idify(tmp_path: Path) -> None:
    results = _make_batch_results().idify(tmp_path)
    with pytest.raises(Exception):
        list(results.tweets(results.entries[0]))
    _assert_tweet_ids(results)


def test_tweets_from_unidify(tmp_path: Path) -> None:
    results = (
        _make_batch_results().idify(tmp_path / "idify").unidify(tmp_path / "unidify")
    )
    _assert_tweet_texts(results)
    _assert_tweet_ids(results)


def test_samedir(tmp_path: Path) -> None:
    _assert_tweet_ids(_make_batch_results().idify())
    results = _make_batch_results().idify(tmp_path).unidify()
    _assert_tweet_ids(results)
    _assert_tweet_texts(results)
