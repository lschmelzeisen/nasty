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

from typing import Optional, Sequence, Tuple

import pytest

from nasty.request.thread import Thread
from nasty.tweet.tweet import TweetId


@pytest.mark.parametrize("max_tweets", [1, 10, 100], ids=repr)
def test_max_tweets(max_tweets: int) -> None:
    tweets = list(
        Thread(TweetId("1183715553057239040"), max_tweets=max_tweets).request()
    )
    assert max_tweets == len(tweets)
    assert len(tweets) == len({tweet.id for tweet in tweets})


@pytest.mark.parametrize("tweet_id", [TweetId("1110485791279595525")], ids=repr)
def test_no_thread(tweet_id: TweetId) -> None:
    assert not list(Thread(tweet_id).request())


@pytest.mark.parametrize(
    "args",
    [
        (
            TweetId("1115689254271819777"),
            [
                TweetId("1115690002233556993"),
                TweetId("1115690615612825601"),
                TweetId("1115691710657499137"),
            ],
        ),
    ],
    ids=repr,
)
def test_exact(args: Tuple[TweetId, Sequence[TweetId]]) -> None:
    tweet_id, thread = args
    assert thread == [tweet.id for tweet in Thread(tweet_id).request()]


@pytest.mark.parametrize(
    "args",
    [
        (TweetId("1155486497451184128"), 35, None),
        (TweetId("1180505950613958658"), 7, None),
    ],
    ids=repr,
)
def test_unlimited(args: Tuple[TweetId, int, Optional[int]]) -> None:
    tweet_id, min_expected, min_tombstones = args
    # Using batch_size=100 to speed up these larger requests.
    tweets = list(Thread(tweet_id, max_tweets=None, batch_size=100).request())
    assert min_expected <= len(tweets)
    # TODO: assert min_tombstones
    assert len(tweets) == len({tweet.id for tweet in tweets})
