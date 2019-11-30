import unittest
from collections import defaultdict
from datetime import date
from enum import Enum, auto
from logging import getLogger
from typing import Any, Dict, List, Tuple

import nasty
import tweepy
from nasty.init import init_nasty
from nasty.old.advanced_search import perform_advanced_search
from nasty.old.tweet import Tweet
from nasty.tests.old.twitter_api import download_api_tweets, setup_tweepy_api


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
        self._run_test("ape", date(year=2017, month=11, day=23), "en")

    def test_metal(self):
        self._run_test("metal", date(year=2018, month=11, day=23), "en")

    def test_i_hope_i_win(self):
        self._run_test("i hope i win", date(year=2019, month=6, day=23), "en")

    @unittest.skip("Takes 5 minutes to run.")
    def test_html_trump(self):
        self._run_test("trump", date(year=2017, month=8, day=22), "en")

    def _run_test(self, keyword: str, date: date, lang: str):
        html_tweets = perform_advanced_search(keyword, date, lang)
        api_tweets = download_api_tweets(self.tweepy_api, html_tweets)

        self.assertNotEqual(0, len(html_tweets))
        self.assertEqual(len(api_tweets), len(html_tweets))

        tweets_by_equal_type = defaultdict(list)
        for html_tweet, api_tweet in zip(
            sorted(html_tweets, key=lambda t: t.id),
            sorted(api_tweets, key=lambda t: t.id_str),
        ):
            tweets_by_equal_type[self._compare_tweets(html_tweet, api_tweet)].append(
                (html_tweet, api_tweet)
            )

        self.log_tweets_by_equal_type(tweets_by_equal_type)
        self.assertEqual(0, len(tweets_by_equal_type[self.TweetEqualType.UNEQUAL]))

    def _compare_tweets(
        self, html_tweet: Tweet, api_tweet: tweepy.Status
    ) -> TweetEqualType:
        self.assertEqual(api_tweet.created_at, html_tweet.created_at)
        self.assertEqual(api_tweet.id_str, html_tweet.id)
        self.assertEqual(api_tweet.user.name, html_tweet.name)
        self.assertEqual(api_tweet.user.screen_name, html_tweet.screen_name)

        # Can't assert equals of indices because we don't guarantee the text
        # to exactly match
        self.assertEqual(len(api_tweet.entities["hashtags"]), len(html_tweet.hashtags))
        for html_hashtag, api_hashtag in zip(
            html_tweet.hashtags, api_tweet.entities["hashtags"]
        ):
            self.assertEqual(api_hashtag["text"], html_hashtag.text)
        self.assertDictEqual(
            self._build_api_url_dict(api_tweet), self._build_html_url_dict(html_tweet)
        )

        if html_tweet.full_text == api_tweet.full_text:
            return self.TweetEqualType.EQUAL
        elif self._remove_mentions(html_tweet.full_text) == self._remove_mentions(
            api_tweet.full_text
        ):
            return self.TweetEqualType.EQUAL_EXCLUDING_MENTIONS
        else:
            return self.TweetEqualType.UNEQUAL

    @classmethod
    def _build_html_url_dict(cls, tweet: Tweet) -> Dict[str, Dict[str, Any]]:
        return {
            url.url: {
                "display_url": url.display_url,
                "expanded_url": url.expanded_url,
                "url": url.url,
            }
            for url in tweet.urls
        }

    @classmethod
    def _build_api_url_dict(cls, tweet: tweepy.Status) -> Dict[str, Dict[str, Any]]:
        return {
            url["url"]: {
                "display_url": url["display_url"],
                "expanded_url": url["expanded_url"],
                "url": url["url"],
            }
            for url in (tweet.entities["urls"] + tweet.entities.get("media", []))
        }

    @staticmethod
    def _remove_mentions(text: str) -> str:
        while text.startswith("@"):
            text = text[text.index(" ") + len(" ") :]
        return text

    @classmethod
    def log_tweets_by_equal_type(
        cls,
        tweets_by_equal_type: Dict[TweetEqualType, List[Tuple[Tweet, tweepy.Status]]],
    ) -> None:
        logger = getLogger(nasty.__name__)

        num_tweets = sum(map(len, tweets_by_equal_type.values()))

        x = len(tweets_by_equal_type[cls.TweetEqualType.EQUAL])
        logger.info(
            "{:d} out of {:d} (≙ {:.2%}) downloaded Tweets did have "
            "exactly matching text as the Twitter API result.".format(
                x, num_tweets, x / num_tweets
            )
        )

        x = len(tweets_by_equal_type[cls.TweetEqualType.EQUAL_EXCLUDING_MENTIONS])
        logger.info(
            "{:d} out of {:d} (≙ {:.2%}) downloaded Tweets did have "
            "exactly matching text as the Twitter API result (when "
            "excluding @mentions):".format(x, num_tweets, x / num_tweets)
        )
        cls.log_tweet_difference(
            tweets_by_equal_type[cls.TweetEqualType.EQUAL_EXCLUDING_MENTIONS],
            plus_mentions_removed=False,
        )

        x = len(tweets_by_equal_type[cls.TweetEqualType.UNEQUAL])
        logger.info(
            "{:d} out of {:d} (≙ {:.2%}) downloaded Tweets did not "
            "have matching text as the Twitter API result even when "
            "excluding @mentions:".format(x, num_tweets, x / num_tweets)
        )
        cls.log_tweet_difference(
            tweets_by_equal_type[cls.TweetEqualType.UNEQUAL], plus_mentions_removed=True
        )

    @classmethod
    def log_tweet_difference(
        cls, tweets: List[Tuple[Tweet, tweepy.Status]], plus_mentions_removed: bool
    ) -> None:
        logger = getLogger(nasty.__name__)

        for html_tweet, api_tweet in tweets:
            logger.debug("Tweet {} {}".format(html_tweet.id, html_tweet.permalink))

            logger.debug("  HTML: {}".format(html_tweet.full_text.replace("\n", "\\n")))
            logger.debug("  API:  {}".format(api_tweet.full_text.replace("\n", "\\n")))

            if plus_mentions_removed:
                logger.debug("  Text excluding @mentions:")
                logger.debug(
                    "    HTML: {}".format(
                        cls._remove_mentions(html_tweet.full_text.replace("\n", "\\n"))
                    )
                )
                logger.debug(
                    "    API:  {}".format(
                        cls._remove_mentions(api_tweet.full_text.replace("\n", "\\n"))
                    )
                )


if __name__ == "__main__":
    unittest.main()
