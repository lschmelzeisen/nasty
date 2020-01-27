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

from typing import Set, Tuple

import pytest

from nasty.request.replies import Replies
from nasty.tweet.tweet import TweetId


@pytest.mark.parametrize("max_tweets", [1, 10, 100], ids=repr)
def test_max_tweets(max_tweets: int) -> None:
    tweets = list(
        Replies(TweetId("1096092704709070851"), max_tweets=max_tweets).request()
    )
    assert max_tweets == len(tweets)
    assert len(tweets) == len({tweet.id for tweet in tweets})


@pytest.mark.parametrize("tweet_id", [TweetId("1110485791279595525")], ids=repr)
def test_no_replies(tweet_id: TweetId) -> None:
    assert not list(Replies(tweet_id).request())


@pytest.mark.parametrize(
    "args",
    [
        (
            TweetId("1115689254271819777"),
            {
                TweetId("1115690002233556993"),
                TweetId("1115947355000406016"),
                TweetId("1115692135808999424"),
                TweetId("1115903315773153280"),
                TweetId("1115692500730171392"),
            },
        ),
    ],
    ids=repr,
)
def test_exact(args: Tuple[TweetId, Set[TweetId]]) -> None:
    tweet_id, replies = args
    assert replies == {tweet.id for tweet in Replies(tweet_id).request()}


@pytest.mark.parametrize(
    "args",
    [
        (TweetId("1155486497451184128"), 150, 2),
        (TweetId("1180505950613958658"), 150, 2),
        (TweetId("550399835682390016"), 150, 15),
    ],
    ids=repr,
)
def test_unlimited(args: Tuple[TweetId, int, int]) -> None:
    tweet_id, min_expected, min_tombstones = args
    # Using batch_size=100 to speed up these larger requests.
    tweets = list(Replies(tweet_id, max_tweets=None, batch_size=100).request())
    assert min_expected <= len(tweets)
    # TODO: assert min_tombstones
    assert len(tweets) == len({tweet.id for tweet in tweets})
