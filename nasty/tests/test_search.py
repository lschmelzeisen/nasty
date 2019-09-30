import unittest
from datetime import date, datetime, timedelta, timezone

from nasty.init import init_nasty
from nasty.search import Query, search
from nasty.tweet import Tweet


class TestQueryJsonConversion(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_nasty()

    def test_trump(self):
        query = Query('trump')
        self.assertEqual(query, Query.from_json(Query.to_json(query)))

    def test_trump_since_until(self):
        query = Query('trump', since=date(2019, 1, 1), until=date(2019, 1, 2))
        self.assertEqual(query, Query.from_json(Query.to_json(query)))

    def test_trump_filter_lang(self):
        query = Query('trump', filter=Query.Filter.LATEST, lang='de')
        self.assertEqual(query, Query.from_json(Query.to_json(query)))


class TestQueryFilterJsonConversion(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_nasty()

    def test_query_filter(self):
        for filter in Query.Filter:
            self.assertEqual(filter, Query.Filter.from_json(filter.to_json()))


class TestQueryUrlParamConversion(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_nasty()

    def test_trump(self):
        query = Query('trump')
        self.assertEqual('trump lang:en', query.url_param)

    def test_trump_since_until(self):
        query = Query('trump', since=date(2019, 1, 1), until=date(2019, 1, 2))
        self.assertEqual('trump since:2019-01-01 until:2019-01-02 lang:en',
                         query.url_param)

    def test_trump_filter_lang(self):
        query = Query('trump', filter=Query.Filter.LATEST, lang='de')
        self.assertEqual('trump lang:de', query.url_param)


# Due to the nature of these tests being dependent on Twitter's sorting rules,
# some of them will break in rare circumstances (especially test_not_*()).
# Usually, rerunning the test will show it to work.


class TestSearchMaxTweets(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_nasty()

    def test_0(self):
        self._run_test(0)

    def test_10(self):
        self._run_test(10)

    def test_100(self):
        self._run_test(100)

    def test_1000(self):
        self._run_test(1000)

    def _run_test(self, max_tweets: int):
        query = Query('trump', since=date(2019, 1, 1), until=date(2019, 1, 2))

        # page_size=100 to speed up these larger requests and since we don't
        # particularly care about accuracy to query here.
        tweets = list(search(query, max_tweets=max_tweets, page_size=100))

        self.assertEqual(max_tweets, len(tweets))

        # Assert that there are no duplicates.
        self.assertEqual(max_tweets, len({tweet.id for tweet in tweets}))


class TestSearchQueryString(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_nasty()

    def test_single_trump(self):
        self._run_test_single('trump')

    def test_single_hillary(self):
        self._run_test_single('hillary')

    def test_single_obama(self):
        self._run_test_single('obama')

    def _run_test_single(self, keyword: str):
        query = Query(keyword)
        tweets = list(search(query, max_tweets=50))
        self.assertEqual(50, len(tweets))
        for tweet in tweets:
            self.assertNotEqual(0, self._count_in_tweet(keyword, tweet))

    def test_and_trump_hillary(self):
        self._run_test_and('trump', 'hillary')

    def test_and_trump_obama(self):
        self._run_test_and('trump', 'obama')

    def test_and_obama_hillary(self):
        self._run_test_and('obama', 'hillary')

    def _run_test_and(self, keyword1: str, keyword2: str):
        query = Query('{} and {}'.format(keyword1, keyword2))
        tweets = list(search(query, max_tweets=50))
        self.assertEqual(50, len(tweets))
        for tweet in tweets:
            self.assertNotEqual(0, self._count_in_tweet(keyword1, tweet))
            self.assertNotEqual(0, self._count_in_tweet(keyword2, tweet))

    def test_or_trump_hillary(self):
        self._run_test_or('trump', 'hillary')

    def test_or_trump_obama(self):
        self._run_test_or('trump', 'obama')

    def test_or_obama_hillary(self):
        self._run_test_or('obama', 'hillary')

    def _run_test_or(self, keyword1: str, keyword2: str):
        query = Query('{} or {}'.format(keyword1, keyword2))
        tweets = list(search(query, max_tweets=50))
        self.assertEqual(50, len(tweets))
        for tweet in tweets:
            self.assertNotEqual(0, (self._count_in_tweet(keyword1, tweet)
                                    + self._count_in_tweet(keyword2, tweet)))

    def test_not_trump_hillary(self):
        self._run_test_not('trump', 'hillary')

    def test_not_trump_obama(self):
        self._run_test_not('trump', 'obama')

    def test_not_obama_hillary(self):
        self._run_test_not('obama', 'hillary')

    def _run_test_not(self, keyword1: str, keyword2: str):
        query = Query('{} -{}'.format(keyword1, keyword2))
        tweets = list(search(query, max_tweets=50))
        self.assertEqual(50, len(tweets))
        for tweet in tweets:
            self.assertNotEqual(0, self._count_in_tweet(keyword1, tweet))
            self.assertEqual(0, tweet.text.lower().count(keyword2.lower()))

    def test_phrase_trump(self):
        self._run_test_phrase('donald', 'trump')

    def test_phrase_hillary(self):
        self._run_test_phrase('hillary', 'clinton')

    def test_phrase_obama(self):
        self._run_test_phrase('Barack', 'Obama')

    def _run_test_phrase(self, keyword1, keyword2):
        query = Query('"{} {}"'.format(keyword1, keyword2))
        tweets = list(search(query, max_tweets=50))
        self.assertEqual(50, len(tweets))
        for tweet in tweets:
            self.assertNotEqual(0, self._count_in_tweet(
                '{} {}'.format(keyword1, keyword2), tweet))

    @classmethod
    def _count_in_tweet(cls, needle: str, tweet: Tweet) -> int:
        haystack = [tweet.text, tweet.user.name, tweet.user.screen_name]
        haystack.extend(url['expanded_url']
                        for url in tweet.json['entities']['urls'])
        if 'card' in tweet.json:
            haystack.append(
                tweet.json['card']['binding_values']['title']['string_value'])
        haystack = ' '.join(haystack)
        return haystack.lower().count(needle.lower())


class TestSearchQueryUser(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_nasty()

    def test_from_trump(self):
        self._run_test_from('realDonaldTrump')

    def test_from_hillary(self):
        self._run_test_from('HillaryClinton')

    def test_from_obama(self):
        self._run_test_from('BarackObama')

    def _run_test_from(self, user: str):
        query = Query('from:@{}'.format(user))
        tweets = list(search(query, max_tweets=50))
        self.assertEqual(50, len(tweets))
        for tweet in tweets:
            self.assertEqual(user.lower(), tweet.user.screen_name.lower())

    def test_to_trump(self):
        self._run_test_to('realDonaldTrump')

    def test_to_hillary(self):
        self._run_test_to('HillaryClinton')

    def test_to_obama(self):
        self._run_test_to('BarackObama')

    def _run_test_to(self, user: str):
        query = Query('to:@{}'.format(user))
        tweets = list(search(query, max_tweets=50))
        self.assertEqual(50, len(tweets))
        for tweet in tweets:
            self.assertNotEqual(
                0, tweet.text.lower().count('@'.format(user).lower()))


class TestSearchDateRange(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_nasty()

    def test_2019(self):
        self._run_test(date(2019, 1, 1), date(2019, 12, 31))

    def test_2019_01_01(self):
        self._run_test(date(2019, 1, 1), date(2019, 1, 2))

    def test_2015(self):
        self._run_test(date(2015, 1, 1), date(2015, 12, 31))

    def test_2015_01_01(self):
        self._run_test(date(2015, 1, 1), date(2015, 1, 2))

    def test_2010(self):
        self._run_test(date(2010, 1, 1), date(2010, 12, 31))

    def test_2010_01_01(self):
        self._run_test(date(2010, 1, 1), date(2010, 1, 2))

    def test_today(self):
        # Assumes that each day there are at least 50 Tweets about "trump".
        self._run_test(date.today() - timedelta(days=1),
                       date.today() + timedelta(days=1))

    def _run_test(self, since: date, until: date):
        query = Query('trump', since=since, until=until)
        tweets = list(search(query, max_tweets=50))
        self.assertEqual(50, len(tweets))
        for tweet in tweets:
            self.assertLessEqual(since, tweet.created_at.date())
            self.assertGreater(until, tweet.created_at.date())

    def test_within_day(self):
        query = Query('trump', since=date(2019, 1, 1), until=date(2019, 1, 1))
        self.assertEqual(0, sum(1 for _ in search(query)))

    def test_future(self):
        query = Query('trump', since=(date.today() + timedelta(days=7)))
        self.assertEqual(0, sum(1 for _ in search(query)))


class TestSearchFilter(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_nasty()

    def test_top(self):
        query = Query('trump', filter=Query.Filter.TOP)
        tweets = list(search(query, max_tweets=50))
        self.assertEqual(50, len(tweets))
        # Since it is unknown how Twitter determines "top" tweets there is no
        # way to check for that.

    def test_latest(self):
        """Check if the 50 latest Tweets about "trump" are from the last 24h."""
        # Assumes that each day there are at least 50 Tweets about "trump".
        yesterday = datetime.now(timezone.utc) - timedelta(days=1)
        query = Query('trump', filter=Query.Filter.LATEST)
        tweets = list(search(query, max_tweets=50))
        self.assertEqual(50, len(tweets))
        for tweet in tweets:
            self.assertLess(yesterday, tweet.created_at)

    def test_photos(self):
        query = Query('trump', filter=Query.Filter.PHOTOS)
        tweets = list(search(query, max_tweets=50))
        self.assertEqual(50, len(tweets))
        for tweet in tweets:
            self.assertNotEqual(
                0, len(tweet.json['extended_entities']['media']))
            for medium in tweet.json['extended_entities']['media']:
                self.assertIn(medium['type'], ['photo', 'animated_gif'])

    def test_videos(self):
        query = Query('trump', filter=Query.Filter.VIDEOS)
        tweets = list(search(query, max_tweets=50))
        self.assertEqual(50, len(tweets))
        for tweet in tweets:
            if 'extended_entities' in tweet.json:
                # Videos hosted on Twitter.
                self.assertNotEqual(
                    0, len(tweet.json['extended_entities']['media']))
                for medium in tweet.json['extended_entities']['media']:
                    self.assertEqual('video', medium['type'])
            else:
                # Video hosted  on external platform.
                # AFAIK there is no general way to check whether an URL to an
                # external platform contains a video.
                pass


class TestSearchLang(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_nasty()

    def test_en(self):
        query = Query('trump', lang='en')
        tweets = list(search(query, max_tweets=50))
        self.assertEqual(50, len(tweets))
        # No robust way to verify language.

    def test_de(self):
        query = Query('trump', lang='de')
        tweets = list(search(query, max_tweets=50))
        self.assertEqual(50, len(tweets))
        # No robust way to verify language.


if __name__ == '__main__':
    unittest.main()
