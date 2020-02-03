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

from itertools import permutations
from pathlib import Path
from typing import Callable, Iterable, Mapping, Optional

import pytest
from _pytest.monkeypatch import MonkeyPatch

import nasty.batch.batch_results
from nasty.batch.batch import Batch
from nasty.batch.batch_results import BatchResults
from nasty.request.replies import Replies
from nasty.request.request import Request
from nasty.request.thread import Thread
from nasty.tweet.tweet import Tweet, TweetId


def _make_batch_results(
    *, idify_dir: Optional[Path] = None, unidify_dir: Optional[Path] = None
) -> BatchResults:
    batch = Batch()
    batch.append(Thread("1115689254271819777"))
    results = batch.execute()
    assert results is not None

    if idify_dir is not None:
        results = results.idify(idify_dir)
        assert results is not None

    if unidify_dir is not None:
        results = results.unidify(unidify_dir)
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
    results = _make_batch_results(idify_dir=tmp_path)
    with pytest.raises(Exception):
        list(results.tweets(results[0]))
    _assert_tweet_ids(results)


def test_tweets_from_unidify(tmp_path: Path) -> None:
    idify_dir = tmp_path / "idify"
    unidify_dir = tmp_path / "unidify"
    results = _make_batch_results(idify_dir=idify_dir, unidify_dir=unidify_dir)
    _assert_tweet_texts(results)
    _assert_tweet_ids(results)


def test_samedir(tmp_path: Path) -> None:
    idify_dir = tmp_path / "idify"
    unidify_dir = tmp_path / "unidify"
    results = _make_batch_results(idify_dir=idify_dir)
    _assert_tweet_ids(results)
    results = _make_batch_results(idify_dir=idify_dir, unidify_dir=unidify_dir)
    _assert_tweet_ids(results)
    _assert_tweet_texts(results)


def test_double_idify(tmp_path: Path) -> None:
    results = _make_batch_results(idify_dir=tmp_path).idify(tmp_path)
    assert results is not None
    with pytest.raises(Exception):
        list(results.tweets(results[0]))
    _assert_tweet_ids(results)


def test_double_unidify(tmp_path: Path) -> None:
    idify_dir = tmp_path / "idify"
    unidify_dir = tmp_path / "unidify"

    results = _make_batch_results(idify_dir=idify_dir, unidify_dir=unidify_dir)
    results = results.unidify(unidify_dir)
    assert results is not None
    _assert_tweet_ids(results)
    _assert_tweet_texts(results)


def _mock_statuses_lookup(
    tweets: Mapping[TweetId, Tweet]
) -> Callable[[Iterable[TweetId]], Iterable[Optional[Tweet]]]:
    def statuses_lookup(tweet_ids: Iterable[TweetId]) -> Iterable[Tweet]:
        return (tweets[tweet_id] for tweet_id in tweet_ids)

    return statuses_lookup


@pytest.mark.parametrize(
    "requests",
    list(
        permutations(
            [
                Replies(TweetId("1115690002233556993")),
                Replies(TweetId("1115690615612825601")),
                Replies(TweetId("1115691710657499137")),
            ]
        )
    ),
    ids=repr,
)
def test_unidify_fail_and_restart(
    requests: Iterable[Request], monkeypatch: MonkeyPatch, tmp_path: Path
) -> None:
    idify_dir = tmp_path / "idify"
    unidify_dir = tmp_path / "unidify"

    batch = Batch()
    for request in requests:
        batch.append(request)
    results = batch.execute()
    assert results is not None

    tweets = {tweet.id: tweet for entry in results for tweet in results.tweets(entry)}
    tweets_truncated = dict(tweets)
    del tweets_truncated[TweetId("1115690615612825601")]

    idified = results.idify(idify_dir)
    assert idified is not None

    monkeypatch.setattr(
        nasty.batch.batch_results,
        nasty.batch.batch_results.statuses_lookup.__name__,  # type: ignore
        _mock_statuses_lookup(tweets_truncated),
    )

    # Assert KeyError is propagated, because a Tweet is missing from tweets_truncated.
    with pytest.raises(KeyError):
        idified.unidify(unidify_dir)
    unidified = BatchResults(unidify_dir)
    assert len(batch) > len(unidified)

    monkeypatch.setattr(
        nasty.batch.batch_results,
        nasty.batch.batch_results.statuses_lookup.__name__,  # type: ignore
        _mock_statuses_lookup(tweets),
    )

    unidified = idified.unidify(unidify_dir)
    assert unidified is not None
    assert len(batch) == len(unidified)
    assert tweets == {
        tweet.id: tweet for entry in unidified for tweet in unidified.tweets(entry)
    }
