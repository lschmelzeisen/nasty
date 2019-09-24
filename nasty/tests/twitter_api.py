from typing import Dict, List, Union

import tweepy

from nasty.init import init_nasty
from nasty.tweet import Tweet
from nasty.util.misc import chunked


def setup_tweepy_api(config: Dict) -> tweepy.API:
    auth = tweepy.OAuthHandler(config['twitter_api']['consumer_key'],
                               config['twitter_api']['consumer_key_secret'])
    auth.set_access_token(config['twitter_api']['access_token'],
                          config['twitter_api']['access_token_secret'])

    api = tweepy.API(auth)
    return api


def download_api_tweets(api: tweepy.API, tweets: List[Union[str, Tweet]]) \
        -> List[tweepy.Status]:
    """Downloads Tweets via the official Twitter API.

    :param api: Tweet API object, created with setup_tweepy_api().
    :param tweets: A list of either Tweet IDs to download or Tweet objects whose
        IDs will be extracted from them.
    :return: List of downloaded Tweets.
    """

    tweet_ids = [tweet.id if isinstance(tweet, Tweet) else tweet
                 for tweet in tweets]

    tweets = []
    for tweet_id_batch in chunked(100, tweet_ids):
        tweets.extend(api.statuses_lookup(tweet_id_batch,
                                          tweet_mode='extended'))

    return tweets


if __name__ == '__main__':
    tweet_ids = ['1129802150018551808']

    config = init_nasty()
    api = setup_tweepy_api(config)
    tweet_list = download_api_tweets(api, tweet_ids)

    from pprint import pprint

    for tweet in tweet_list:
        pprint(tweet._json)
