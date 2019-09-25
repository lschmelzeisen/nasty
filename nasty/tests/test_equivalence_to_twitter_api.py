import unittest
from collections import defaultdict
from datetime import date
from enum import Enum, auto
from logging import getLogger
from typing import Dict, List, Tuple

import tweepy

import nasty
from nasty.advanced_search import perform_advanced_search
from nasty.init import init_nasty
from nasty.tests.twitter_api import download_api_tweets, \
    setup_tweepy_api
from nasty.tweet import Tweet


class TestEquivalenceToTwitterApi(unittest.TestCase):
    class TweetEqualType(Enum):
        EQUAL = auto()
        EQUAL_EXCLUDING_MENTIONS = auto()
        UNEQUAL = auto()

    @classmethod
    def setUpClass(cls):
        cls.config = init_nasty()
        cls.tweepy_api = setup_tweepy_api(cls.config)

    def test_ape(self):
        self._run_test('ape', date(year=2017, month=11, day=23), 'en')

    def test_metal(self):
        self._run_test('metal', date(year=2018, month=11, day=23), 'en')

    def test_i_hope_i_win(self):
        self._run_test('i hope i win', date(year=2019, month=6, day=23), 'en')

    @unittest.skip('Takes 5 minutes to run.')
    def test_html_trump(self):
        self._run_test('trump', date(year=2017, month=8, day=22), 'en')

    def _run_test(self, keyword: str, date: date, lang: str):
        html_tweets = perform_advanced_search(keyword, date, lang)
        api_tweets = download_api_tweets(self.tweepy_api, html_tweets)

        self.assertNotEqual(0, len(html_tweets))
        self.assertEqual(len(html_tweets), len(api_tweets))

        tweets_by_equal_type = defaultdict(list)
        for html_tweet, api_tweet in zip(
                sorted(html_tweets, key=lambda t: t.id),
                sorted(api_tweets, key=lambda t: t.id_str)):
            tweets_by_equal_type[self._compare_tweets(html_tweet, api_tweet)] \
                .append((html_tweet, api_tweet))

        self.log_tweets_by_equal_type(tweets_by_equal_type)
        self.assertEqual(
            0, len(tweets_by_equal_type[self.TweetEqualType.UNEQUAL]))

    def _compare_tweets(self, html_tweet: Tweet, api_tweet: tweepy.Status) \
            -> TweetEqualType:
        self.assertEqual(html_tweet.id, api_tweet.id_str)

        if html_tweet.full_text == api_tweet.full_text:
            return self.TweetEqualType.EQUAL
        elif (self._remove_mentions(html_tweet.full_text)
              == self._remove_mentions(api_tweet.full_text)):
            return self.TweetEqualType.EQUAL_EXCLUDING_MENTIONS
        else:
            return self.TweetEqualType.UNEQUAL

    @classmethod
    def _remove_mentions(cls, text: str) -> str:
        while text.startswith('@'):
            text = text[text.index(' ') + len(' '):]
        return text

    @classmethod
    def log_tweets_by_equal_type(
            cls,
            tweets_by_equal_type: Dict[TweetEqualType,
                                       List[Tuple[Tweet, tweepy.Status]]]) \
            -> None:
        logger = getLogger(nasty.__name__)

        num_tweets = sum(map(len, tweets_by_equal_type.values()))

        x = len(tweets_by_equal_type[cls.TweetEqualType.EQUAL])
        logger.info('{:d} out of {:d} (≙ {:.2%}) downloaded Tweets did have '
                    'exactly matching text as the Twitter API result.'.format(
            x, num_tweets, x / num_tweets))

        x = len(tweets_by_equal_type[
                    cls.TweetEqualType.EQUAL_EXCLUDING_MENTIONS])
        logger.info('{:d} out of {:d} (≙ {:.2%}) downloaded Tweets did have '
                    'exactly matching text as the Twitter API result (when '
                    'excluding @mentions):'.format(
            x, num_tweets, x / num_tweets))
        cls.log_tweet_difference(
            tweets_by_equal_type[cls.TweetEqualType.EQUAL_EXCLUDING_MENTIONS],
            plus_mentions_removed=False)

        x = len(tweets_by_equal_type[cls.TweetEqualType.UNEQUAL])
        logger.info('{:d} out of {:d} (≙ {:.2%}) downloaded Tweets did not '
                    'have matching text as the Twitter API result even when '
                    'excluding @mentions:'.format(
            x, num_tweets, x / num_tweets))
        cls.log_tweet_difference(
            tweets_by_equal_type[cls.TweetEqualType.UNEQUAL],
            plus_mentions_removed=True)

    @classmethod
    def log_tweet_difference(cls,
                             tweets: List[Tuple[Tweet, tweepy.Status]],
                             plus_mentions_removed: bool) -> None:
        logger = getLogger(nasty.__name__)

        for html_tweet, api_tweet in tweets:
            logger.debug('Tweet {} {}'.format(
                html_tweet.id, html_tweet.permalink))

            logger.debug('  HTML: {}'.format(
                html_tweet.full_text.replace('\n', '\\n')))
            logger.debug('  API:  {}'.format(
                api_tweet.full_text.replace('\n', '\\n')))

            if plus_mentions_removed:
                logger.debug('  Text excluding @mentions:')
                logger.debug('    HTML: {}'.format(cls._remove_mentions(
                    html_tweet.full_text.replace('\n', '\\n'))))
                logger.debug('    API:  {}'.format(cls._remove_mentions(
                    api_tweet.full_text.replace('\n', '\\n'))))


if __name__ == '__main__':
    unittest.main()
