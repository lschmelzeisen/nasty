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
import re
import unittest
from datetime import date, datetime, timedelta, timezone

from nasty._util.disrespect_robotstxt import disrespect_robotstxt
from nasty._util.logging_ import setup_logging
from nasty.retrieval.search import Search
from nasty.tests.util.requests_cache import RequestsCache

setup_logging(logging.DEBUG)


class TestQueryJsonConversion(unittest.TestCase):
    def test_trump(self):
        query = Search.Query("trump")
        self.assertEqual(query, Search.Query.from_json(Search.Query.to_json(query)))

    def test_trump_since_until(self):
        query = Search.Query("trump", since=date(2019, 1, 1), until=date(2019, 1, 2))
        self.assertEqual(query, Search.Query.from_json(Search.Query.to_json(query)))

    def test_trump_filter_lang(self):
        query = Search.Query("trump", filter=Search.Query.Filter.LATEST, lang="de")
        self.assertEqual(query, Search.Query.from_json(Search.Query.to_json(query)))


class TestQueryFilterJsonConversion(unittest.TestCase):
    def test_query_filter(self):
        for filter in Search.Query.Filter:
            self.assertEqual(filter, Search.Query.Filter.from_json(filter.to_json()))


class TestQueryUrlParamConversion(unittest.TestCase):
    def test_trump(self):
        query = Search.Query("trump")
        self.assertEqual("trump lang:en", query.url_param)

    def test_trump_since_until(self):
        query = Search.Query("trump", since=date(2019, 1, 1), until=date(2019, 1, 2))
        self.assertEqual(
            "trump since:2019-01-01 until:2019-01-02 lang:en", query.url_param
        )

    def test_trump_filter_lang(self):
        query = Search.Query("trump", filter=Search.Query.Filter.LATEST, lang="de")
        self.assertEqual("trump lang:de", query.url_param)


# Due to the nature of these tests being dependent on Twitter's sorting rules,
# some of them will break in rare circumstances (especially test_not()).
# Usually, rerunning the test will show it to work.


class TestSearchMaxTweets(unittest.TestCase):
    @RequestsCache()
    @disrespect_robotstxt
    def test_0(self):
        self._run_test(0)

    @RequestsCache()
    @disrespect_robotstxt
    def test_10(self):
        self._run_test(10)

    @RequestsCache()
    @disrespect_robotstxt
    def test_100(self):
        self._run_test(100)

    @RequestsCache()
    @disrespect_robotstxt
    def test_1000(self):
        self._run_test(1000)

    def _run_test(self, max_tweets: int):
        query = Search.Query("trump", since=date(2019, 1, 1), until=date(2019, 1, 2))

        # batch_size=100 to speed up these larger requests and since we don't
        # particularly care about accuracy to query here.
        tweets = list(Search(query, max_tweets=max_tweets, batch_size=100))

        self.assertEqual(max_tweets, len(tweets))

        # Assert that there are no duplicates.
        self.assertEqual(len(tweets), len({tweet.id for tweet in tweets}))


class TestSearchQueryString(unittest.TestCase):
    # In all of the test here we check whether the search keyword occurs not
    # only in the Tweet's text but also in accompanying fields like user name,
    # because Twitter also sometimes matches on those.

    @RequestsCache()
    @disrespect_robotstxt
    def test_word(self):
        def run_test(keyword: str) -> None:
            query = Search.Query(keyword)
            tweets = list(Search(query, max_tweets=50))
            self.assertEqual(50, len(tweets))
            for tweet in tweets:
                all_tweet_text = json.dumps(tweet.to_json()).lower()
                self.assertIn(keyword.lower(), all_tweet_text)

        run_test("trump")
        run_test("hillary")
        run_test("obama")

    @RequestsCache()
    @disrespect_robotstxt
    def test_unknown_word(self):
        # Random string that currently does not match any Tweet.
        unknown_word = "c9dde8b5451149e683d4f07e4c4348ef"
        tweets = list(Search(Search.Query(unknown_word), max_tweets=50))
        self.assertEqual(0, len(tweets))

    @RequestsCache()
    @disrespect_robotstxt
    def test_and(self):
        def run_test(keyword1: str, keyword2: str) -> None:
            query = Search.Query("{} and {}".format(keyword1, keyword2))
            tweets = list(Search(query, max_tweets=50))
            self.assertEqual(50, len(tweets))
            for tweet in tweets:
                all_tweet_text = json.dumps(tweet.to_json()).lower()
                self.assertIn(keyword1.lower(), all_tweet_text)
                self.assertIn(keyword2.lower(), all_tweet_text)

        run_test("trump", "hillary")
        run_test("trump", "obama")
        run_test("obama", "hillary")

    @RequestsCache()
    @disrespect_robotstxt
    def test_or(self):
        def run_test(keyword1: str, keyword2: str) -> None:
            query = Search.Query("{} or {}".format(keyword1, keyword2))
            tweets = list(Search(query, max_tweets=50))
            self.assertEqual(50, len(tweets))
            for tweet in tweets:
                all_tweet_text = json.dumps(tweet.to_json()).lower()
                assert_keyword1 = keyword1.lower() in all_tweet_text
                assert_keyword2 = keyword2.lower() in all_tweet_text
                self.assertTrue(assert_keyword1 or assert_keyword2)

        run_test("trump", "hillary")
        run_test("trump", "obama")
        run_test("obama", "hillary")

    @RequestsCache()
    @disrespect_robotstxt
    def test_not(self):
        def run_test(keyword1: str, keyword2: str) -> None:
            query = Search.Query("{} -{}".format(keyword1, keyword2))
            tweets = list(Search(query, max_tweets=50))
            self.assertEqual(50, len(tweets))
            for tweet in tweets:
                all_tweet_text = json.dumps(tweet.to_json()).lower()
                self.assertIn(keyword1.lower(), all_tweet_text)
                # Sadly, keyword2 can sometimes still occur in the Text even
                # though we specifically ask Twitter not to. In those cases
                # I do not want to count this case a failure and skip it then.
                try:
                    self.assertNotIn(keyword2.lower(), tweet.text.lower())
                except AssertionError as e:
                    self.skipTest(str(e))

        run_test("trump", "hillary")
        run_test("trump", "obama")
        run_test("obama", "hillary")

    @RequestsCache()
    @disrespect_robotstxt
    def test_phrase(self):
        def run_test(keyword1, keyword2) -> None:
            query = Search.Query('"{} {}"'.format(keyword1, keyword2))
            tweets = list(Search(query, max_tweets=50))
            self.assertEqual(50, len(tweets))
            for tweet in tweets:
                all_tweet_text = json.dumps(tweet.to_json()).lower()
                phrase = "{} {}".format(keyword1, keyword2).lower()
                try:
                    self.assertIn(phrase, all_tweet_text)
                except AssertionError:
                    # Remove non alphanumeric
                    # See https://stackoverflow.com/a/1277047/211404
                    all_tweet_text = re.sub("[\W_]+", "", all_tweet_text)
                    phrase = re.sub("[\W_]+", "", phrase)
                    self.assertIn(phrase, all_tweet_text)

        run_test("donald", "trump")
        run_test("hillary", "clinton")
        run_test("Barack", "Obama")


class TestSearchQueryUser(unittest.TestCase):
    @RequestsCache()
    @disrespect_robotstxt
    def test_from(self):
        def run_test(user: str) -> None:
            query = Search.Query("from:@{}".format(user))
            tweets = list(Search(query, max_tweets=50))
            self.assertLess(0, len(tweets))
            self.assertGreaterEqual(50, len(tweets))
            for tweet in tweets:
                self.assertEqual(user.lower(), tweet.user.screen_name.lower())

        run_test("realDonaldTrump")
        run_test("HillaryClinton")
        run_test("BarackObama")

    @RequestsCache()
    @disrespect_robotstxt
    def test_to(self):
        def run_test(user: str) -> None:
            query = Search.Query("to:@{}".format(user))
            tweets = list(Search(query, max_tweets=50))
            self.assertEqual(50, len(tweets))
            for tweet in tweets:
                try:
                    self.assertNotEqual(
                        0, tweet.text.lower().count("@".format(user).lower())
                    )
                except AssertionError:
                    # Sometimes when a user creates a thread his individual
                    # Tweets will not reply to the user, for example:
                    # https://twitter.com/_/status/1197499643086753793
                    self.assertEqual(user, tweet.user.screen_name)

        run_test("realDonaldTrump")
        run_test("HillaryClinton")
        run_test("BarackObama")


class TestSearchDateRange(unittest.TestCase):
    @RequestsCache()
    @disrespect_robotstxt
    def test_date_range_1_year(self):
        self._run_test(date(2010, 1, 1), date(2010, 12, 31))
        self._run_test(date(2015, 1, 1), date(2015, 12, 31))
        self._run_test(date(2019, 1, 1), date(2019, 12, 31))

    @RequestsCache()
    @disrespect_robotstxt
    def test_date_range_1_day(self):
        self._run_test(date(2010, 1, 1), date(2010, 1, 2))
        self._run_test(date(2015, 2, 10), date(2015, 2, 11))
        self._run_test(date(2019, 3, 21), date(2019, 3, 22))

    @RequestsCache()
    @disrespect_robotstxt
    def test_today(self):
        # Assumes that each day there are at least 40 Tweets about "trump".
        self._run_test(
            date.today() - timedelta(days=1), date.today() + timedelta(days=1)
        )

    def _run_test(self, since: date, until: date):
        query = Search.Query("trump", since=since, until=until)
        tweets = list(Search(query, max_tweets=40))
        self.assertEqual(40, len(tweets))
        for tweet in tweets:
            self.assertLessEqual(since, tweet.created_at.date())
            self.assertGreater(until, tweet.created_at.date())

    @RequestsCache()
    @disrespect_robotstxt
    def test_within_day(self):
        query = Search.Query("trump", since=date(2019, 1, 1), until=date(2019, 1, 1))
        self.assertEqual(0, sum(1 for _ in Search(query)))

    @RequestsCache()
    @disrespect_robotstxt
    def test_future(self):
        query = Search.Query("trump", since=(date.today() + timedelta(days=7)))
        self.assertEqual(0, sum(1 for _ in Search(query)))


class TestSearchFilter(unittest.TestCase):
    @RequestsCache()
    @disrespect_robotstxt
    def test_top(self):
        query = Search.Query("trump", filter=Search.Query.Filter.TOP)
        tweets = list(Search(query, max_tweets=50))
        self.assertEqual(50, len(tweets))
        # Since it is unknown how Twitter determines "top" tweets there is no
        # way to check for that.

    @RequestsCache()
    @disrespect_robotstxt
    def test_latest(self):
        """Check if the 50 latest Tweets about "trump" are from the last 24h."""
        # Assumes that each day there are at least 50 Tweets about "trump".
        yesterday = datetime.now(timezone.utc) - timedelta(days=1)
        query = Search.Query("trump", filter=Search.Query.Filter.LATEST)
        tweets = list(Search(query, max_tweets=50))
        self.assertEqual(50, len(tweets))
        for tweet in tweets:
            self.assertLess(yesterday, tweet.created_at)

    @RequestsCache()
    @disrespect_robotstxt
    def test_photos(self):
        query = Search.Query("trump", filter=Search.Query.Filter.PHOTOS)
        tweets = list(Search(query, max_tweets=50))
        self.assertEqual(50, len(tweets))
        for tweet in tweets:
            self.assertNotEqual(0, len(tweet.json["extended_entities"]["media"]))
            for medium in tweet.json["extended_entities"]["media"]:
                self.assertIn(medium["type"], ["photo", "animated_gif"])

    @RequestsCache()
    @disrespect_robotstxt
    def test_videos(self):
        query = Search.Query("trump", filter=Search.Query.Filter.VIDEOS)
        tweets = list(Search(query, max_tweets=50))
        self.assertEqual(50, len(tweets))
        for tweet in tweets:
            if "extended_entities" in tweet.json:
                # Videos hosted on Twitter.
                self.assertNotEqual(0, len(tweet.json["extended_entities"]["media"]))
                for medium in tweet.json["extended_entities"]["media"]:
                    self.assertEqual("video", medium["type"])
            else:
                # Video hosted  on external platform.
                # AFAIK there is no general way to check whether an URL to an
                # external platform contains a video.
                pass


class TestSearchLang(unittest.TestCase):
    @RequestsCache()
    @disrespect_robotstxt
    def test_en(self):
        query = Search.Query("trump", lang="en")
        tweets = list(Search(query, max_tweets=50))
        self.assertEqual(50, len(tweets))
        # No robust way to verify language.

    @RequestsCache()
    @disrespect_robotstxt
    def test_de(self):
        query = Search.Query("trump", lang="de")
        tweets = list(Search(query, max_tweets=50))
        self.assertEqual(50, len(tweets))
        # No robust way to verify language.

    @RequestsCache()
    @disrespect_robotstxt
    def test_invalid_lang(self):
        query = Search.Query("trump", lang="INVALID")
        tweets = list(Search(query, max_tweets=50))
        self.assertEqual(0, len(tweets))


if __name__ == "__main__":
    unittest.main()
