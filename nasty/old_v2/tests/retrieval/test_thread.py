import logging
import unittest
from typing import Optional

from nasty.tests.util.requests_cache import RequestsCache
from nasty.retrieval.thread import Thread
from nasty._util.disrespect_robotstxt import disrespect_robotstxt
from nasty._util.logging_ import setup_logging

setup_logging(logging.DEBUG)


class TestNoThread(unittest.TestCase):
    @RequestsCache()
    @disrespect_robotstxt
    def test_1110485791279595525(self):
        tweets = list(Thread('1110485791279595525'))
        self.assertEqual(0, len(tweets))


class TestExactThread(unittest.TestCase):
    @RequestsCache()
    @disrespect_robotstxt
    def test_1115689254271819777(self):
        tweets = list(tweet.id for tweet in Thread('1115689254271819777'))
        self.assertEqual(tweets,
                         ['1115690002233556993',
                          '1115690615612825601',
                          '1115691710657499137'])


class TestThreadMaxTweets(unittest.TestCase):
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

    def _run_test(self, max_tweets: int):
        tweets = list(Thread('1183715553057239040', max_tweets=max_tweets))

        self.assertEqual(max_tweets, len(tweets))

        # Assert that there are no duplicates.
        self.assertEqual(len(tweets), len({tweet.id for tweet in tweets}))


class TestThreadUnlimited(unittest.TestCase):
    # The minimum expected numbers where gathered with executing this code once.
    # Thus, the following are just regression tests, as I don't know of any
    # other reliable way to carry these numbers.

    @RequestsCache()
    @disrespect_robotstxt
    def test_1155486497451184128(self):
        self._run_test('1155486497451184128', 35, None)

    @RequestsCache()
    @disrespect_robotstxt
    def test_1180505950613958658(self):
        self._run_test('1180505950613958658', 8, None)

    def _run_test(self,
                  tweet_id: str,
                  min_expected: int,
                  min_tombstones: Optional[int]):
        # batch_size=100 to speed up these larger requests.
        thread = Thread(tweet_id, max_tweets=None, batch_size=100)
        tweets = list(thread)

        self.assertLessEqual(min_expected, len(tweets))
        if min_tombstones is not None:
            self.assertLessEqual(min_tombstones, thread.num_tombstones)
        else:
            self.assertIsNone(thread.num_tombstones)

        # Assert that there are no duplicates.
        self.assertEqual(len(tweets), len({tweet.id for tweet in tweets}))
