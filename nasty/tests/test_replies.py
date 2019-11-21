import unittest

from nasty.init import init_nasty
from nasty.replies import Replies
from nasty.tests.requests_cache import RequestsCache

init_nasty()


class TestNoReplies(unittest.TestCase):
    @RequestsCache()
    def test_1110485791279595525(self):
        tweets = list(Replies('1110485791279595525'))
        self.assertEqual(0, len(tweets))


class TestExactReplies(unittest.TestCase):
    @RequestsCache(True)
    def test_1115689254271819777(self):
        tweets = set(tweet.id for tweet in Replies('1115689254271819777'))
        self.assertEqual(tweets,
                         {'1115690002233556993',
                          '1115947355000406016',
                          '1115692135808999424',
                          '1115903315773153280',
                          '1115692500730171392'})


class TestRepliesMaxTweets(unittest.TestCase):
    @RequestsCache()
    def test_0(self):
        self._run_test(0)

    @RequestsCache()
    def test_10(self):
        self._run_test(10)

    @RequestsCache()
    def test_100(self):
        self._run_test(100)

    def _run_test(self, max_tweets: int):
        tweets = list(Replies('1096092704709070851', max_tweets=max_tweets))

        self.assertEqual(max_tweets, len(tweets))

        # Assert that there are no duplicates.
        self.assertEqual(len(tweets), len({tweet.id for tweet in tweets}))


class TestRepliesUnlimited(unittest.TestCase):
    # The minimum expected numbers where gathered with executing this code once.
    # Thus, the following are just regression tests, as I don't know of any
    # other reliable way to carry these numbers.

    @RequestsCache()
    def test_1155486497451184128(self):
        self._run_test('1155486497451184128', 200, 5)

    @RequestsCache()
    def test_1180505950613958658(self):
        self._run_test('1180505950613958658', 200, 4)

    @RequestsCache()
    def test_550399835682390016(self):
        self._run_test('550399835682390016', 200, 26)

    def _run_test(self, tweet_id: str, min_expected: int, min_tombstones: int):
        # batch_size=100 to speed up these larger requests.
        replies = Replies(tweet_id, max_tweets=None, batch_size=100)
        tweets = list(replies)

        self.assertLessEqual(min_expected, len(tweets))
        self.assertLessEqual(min_tombstones, replies.num_tombstones)

        # Assert that there are no duplicates.
        self.assertEqual(len(tweets), len({tweet.id for tweet in tweets}))
