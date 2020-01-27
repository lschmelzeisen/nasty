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
import re
from datetime import date, datetime, timedelta, timezone
from typing import Any, Tuple, cast

import pytest

from nasty.request.search import Search, SearchFilter


@pytest.mark.parametrize("max_tweets", [1, 10, 100, 1000], ids=repr)
def test_max_tweets(max_tweets: int) -> None:
    # Using batch_size=100 to speed up these larger requests and since we don't care
    # about accuracy to query here.
    tweets = list(Search("trump", max_tweets=max_tweets, batch_size=100).request())
    assert max_tweets == len(tweets)
    assert len(tweets) == len({tweet.id for tweet in tweets})


# -- test_query_word_* -----------------------------------------------------------------


@pytest.mark.parametrize("word", ["trump", "hillary", "obama"], ids=repr)
def test_query_word_single(word: str) -> None:
    tweets = list(Search(word, max_tweets=50).request())
    assert 50 == len(tweets)
    for tweet in tweets:
        assert word.lower() in json.dumps(tweet.to_json()).lower()


# Random string that currently does not match any Tweet.
@pytest.mark.parametrize("word", ["c9dde8b5451149e683d4f07e4c4348ef"], ids=repr)
def test_query_word_unkown(word: str) -> None:
    assert not list(Search(word).request())


TEST_QUERY_KEYWORDS = [("trump", "hillary"), ("trump", "obama"), ("obama", "hillary")]


@pytest.mark.parametrize("args", TEST_QUERY_KEYWORDS, ids=repr)
def test_query_word_and(args: Tuple[str, str]) -> None:
    word1, word2 = args
    tweets = list(Search("{} and {}".format(word1, word2), max_tweets=50).request())
    assert 50 == len(tweets)
    for tweet in tweets:
        all_tweet_text = json.dumps(tweet.to_json()).lower()
        assert word1.lower() in all_tweet_text
        assert word2.lower() in all_tweet_text


@pytest.mark.parametrize("args", TEST_QUERY_KEYWORDS, ids=repr)
def test_query_word_or(args: Tuple[str, str]) -> None:
    word1, word2 = args
    tweets = list(Search("{} or {}".format(word1, word2), max_tweets=50).request())
    assert 50 == len(tweets)
    for tweet in tweets:
        all_tweet_text = json.dumps(tweet.to_json()).lower()
        assert word1.lower() in all_tweet_text or word2.lower() in all_tweet_text


@pytest.mark.parametrize("args", TEST_QUERY_KEYWORDS, ids=repr)
def test_query_word_not(args: Tuple[str, str]) -> None:
    word1, word2 = args
    tweets = list(Search("{} -{}".format(word1, word2), max_tweets=50).request())
    assert 50 == len(tweets)
    for tweet in tweets:
        all_tweet_text = json.dumps(tweet.to_json()).lower()
        # Sadly, word2 can sometimes still occur in the Text even though we specifically
        # ask Twitter not to. In those cases I do not want to count this case a failure
        # and skip it then.
        assert word1.lower() in all_tweet_text
        if word2.lower() in tweet.text.lower():
            pytest.skip(
                "Negative query word '{}' found in result tweet: {}".format(
                    word2, tweet.to_json()
                )
            )


@pytest.mark.parametrize(
    "phrase", ["donald trump", "hillary clinton", "barack obama"], ids=repr
)
def test_query_word_phrase(phrase: str) -> None:
    tweets = list(Search(phrase, max_tweets=50).request())
    assert 50 == len(tweets)
    for tweet in tweets:
        all_tweet_text = json.dumps(tweet.to_json()).lower()
        if phrase.lower() in all_tweet_text:
            # Remove non alphanumeric, see https://stackoverflow.com/a/1277047/211404
            all_tweet_text = re.sub(r"[\W_]+", "", all_tweet_text)
            phrase = re.sub(r"[\W_]+", "", phrase.lower())
            assert phrase in all_tweet_text


# -- test_quest_user_* -----------------------------------------------------------------


TEST_QUERY_USERS = ["realDonaldTrump", "HillaryClinton", "BarackObama"]


@pytest.mark.parametrize("user", TEST_QUERY_USERS, ids=repr)
def test_query_user_from(user: str) -> None:
    tweets = list(Search("from:@" + user, max_tweets=50).request())
    assert 0 < len(tweets) <= 50
    for tweet in tweets:
        assert user.lower() == tweet.user.screen_name.lower()


@pytest.mark.parametrize("user", TEST_QUERY_USERS, ids=repr)
def test_query_user_to(user: str) -> None:
    tweets = list(Search("to:@" + user, max_tweets=50).request())
    assert 50 == len(tweets)
    for tweet in tweets:
        if not tweet.text.lower().count("@" + user.lower()):
            # Sometimes when a user creates a thread his individual Tweets will not
            # reply to the user, for example:
            # https://twitter.com/_/status/1197499643086753793
            assert user.lower() == tweet.user.screen_name.lower()


# -- test_date_* -----------------------------------------------------------------------


@pytest.mark.parametrize(
    "args",
    [
        # range: 1 year
        (date(2010, 1, 1), date(2010, 12, 31)),
        (date(2015, 1, 1), date(2015, 12, 31)),
        (date(2019, 1, 1), date(2019, 12, 31)),
        # range: 1 day
        (date(2010, 1, 1), date(2010, 1, 2)),
        (date(2015, 2, 10), date(2015, 2, 11)),
        (date(2019, 3, 21), date(2019, 3, 22)),
        # today
        (date.today() - timedelta(days=1), date.today() + timedelta(days=1)),
    ],
    ids=repr,
)
def test_date_range(args: Tuple[date, date]) -> None:
    since, until = args
    tweets = list(Search("trump", since=since, until=until, max_tweets=40).request())
    assert 40 == len(tweets)
    for tweet in tweets:
        assert since <= tweet.created_at.date() < until


def test_date_future() -> None:
    assert not list(Search("trump", since=(date.today() + timedelta(days=7))).request())


# -- test_filter_* ---------------------------------------------------------------------


def test_filter_top() -> None:
    assert 50 == len(
        list(Search("trump", filter_=SearchFilter.TOP, max_tweets=50).request())
    )
    # Since it is unknown how Twitter determines "top" tweets there is no way to check
    # for that.


def test_filter_latest() -> None:
    # Check if the 50 latest Tweets about "trump" are from the last 24h. Assumes that
    # each day there are at least 50 Tweets about "trump".
    tweets = list(Search("trump", filter_=SearchFilter.LATEST, max_tweets=50).request())
    assert 50 == len(tweets)
    for tweet in tweets:
        assert datetime.now(timezone.utc) - timedelta(days=1) < tweet.created_at


def test_filter_photos() -> None:
    tweets = list(Search("trump", filter_=SearchFilter.PHOTOS, max_tweets=50).request())
    assert 50 == len(tweets)
    for tweet in tweets:
        json = cast(Any, tweet.json)
        assert len(json["extended_entities"]["media"])
        for medium in json["extended_entities"]["media"]:
            assert medium["type"] in {"photo", "animated_gif"}


def test_filter_videos() -> None:
    tweets = list(Search("trump", filter_=SearchFilter.VIDEOS, max_tweets=50).request())
    assert 50 == len(tweets)
    for tweet in tweets:
        if "extended_entities" in tweet.json:
            # Video hosted on Twitter.
            json = cast(Any, tweet.json)
            assert len(json["extended_entities"]["media"])
            if "video" in tweet.text.lower():
                # Had one case, where an image post containing the substring
                # "VIDEO: youtu.be/..." matched this query.
                return
            for medium in json["extended_entities"]["media"]:
                assert "video" == medium["type"]
        else:
            # Video hosted  on external platform. AFAIK there is no general way to check
            # whether an URL to an external platform contains a video.
            pass


# -- test_lang_* -----------------------------------------------------------------------


def test_lang_en() -> None:
    assert 50 == len(list(Search("trump", lang="en", max_tweets=50).request()))
    # No robust way to verify language.


def test_lang_de() -> None:
    assert 50 == len(list(Search("trump", lang="de", max_tweets=50).request()))
    # No robust way to verify language.


def test_lang_invalid() -> None:
    assert not list(Search("trump", lang="INVALID", max_tweets=50).request())
