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
from typing import Callable, Iterable, Mapping, Optional, Tuple

import pytest
from _pytest.monkeypatch import MonkeyPatch
from more_itertools import flatten

import nasty.batch.batch_results
from nasty.batch.batch import Batch
from nasty.batch.batch_results import BatchResults
from nasty.request.replies import Replies
from nasty.request.thread import Thread
from nasty.tweet.tweet import Tweet, TweetId


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
    ] == [tweet.text for tweet in results.tweets(results[0])]


def _assert_tweet_ids(results: BatchResults) -> None:
    assert [
        TweetId("1115690002233556993"),
        TweetId("1115690615612825601"),
        TweetId("1115691710657499137"),
    ] == list(results.tweet_ids(results[0]))


def test_tweets_from_exectue() -> None:
    results = _make_batch_results()
    _assert_tweet_texts(results)
    _assert_tweet_ids(results)


def test_tweets_from_idify(tmp_path: Path) -> None:
    results = _make_batch_results().idify(tmp_path)
    with pytest.raises(Exception):
        list(results.tweets(results[0]))
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


def test_double_idify(tmp_path: Path) -> None:
    results = _make_batch_results()
    results.idify(tmp_path)
    results = results.idify(tmp_path)
    with pytest.raises(Exception):
        list(results.tweets(results[0]))
    _assert_tweet_ids(results)


def test_double_unidify(tmp_path: Path) -> None:
    idify_dir = tmp_path / "idify"
    unidify_dir = tmp_path / "unidify"

    results = _make_batch_results().idify(idify_dir)
    results.unidify(unidify_dir)
    results = results.idify(unidify_dir)
    _assert_tweet_ids(results)
    _assert_tweet_texts(results)


def _mock_statuses_lookup(
    tweets: Mapping[Tuple[TweetId, ...], Iterable[Tweet]],
) -> Callable[[Iterable[TweetId]], Iterable[Optional[Tweet]]]:
    already_failed = False

    def f(tweet_ids: Iterable[TweetId]) -> Iterable[Optional[Tweet]]:
        nonlocal already_failed
        tweet_ids = tuple(tweet_ids)
        if len(tweet_ids) == 2 and not already_failed:
            already_failed = True
            raise ValueError("Test error")

        yield from tweets[tweet_ids]

    return f


def test_unidify_fail_and_restart(monkeypatch: MonkeyPatch, tmp_path: Path) -> None:
    idify_dir = tmp_path / "idify"
    unidify_dir = tmp_path / "unidify"

    batch = Batch()
    batch.append(Replies(TweetId("1115690002233556993")))
    batch.append(Replies(TweetId("1115690615612825601")))
    batch.append(Replies(TweetId("1115691710657499137")))
    results = batch.execute()
    assert results is not None
    tweets = {
        tuple(results.tweet_ids(entry)): list(results.tweets(entry))
        for entry in results
    }

    idified = results.idify(idify_dir)

    monkeypatch.setattr(
        nasty.batch.batch_results,
        nasty.batch.batch_results.statuses_lookup.__name__,  # type: ignore
        _mock_statuses_lookup(tweets),
    )

    with pytest.raises(ValueError):
        idified.unidify(unidify_dir)

    assert 1 == len(BatchResults(unidify_dir))

    unidified = idified.unidify(tmp_path / "unidify")
    assert 3 == len(unidified)
    assert [(tweet.id, tweet.text) for tweet in flatten(tweets.values())] == [
        (tweet.id, tweet.text)
        for entry in unidified
        for tweet in unidified.tweets(entry)
    ]
