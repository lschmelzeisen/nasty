from typing import Dict, Iterator, List, Union

import tweepy

from nasty.init import init_nasty
from nasty.tweet import Tweet


def setup_tweepy_api(config: Dict) -> tweepy.API:
    auth = tweepy.OAuthHandler(config['twitter_api']['consumer_key'],
                               config['twitter_api']['consumer_key_secret'])
    auth.set_access_token(config['twitter_api']['access_token'],
                          config['twitter_api']['access_token_secret'])

    api = tweepy.API(auth)
    return api


def download_api_tweets_from_html_tweets(
        api: tweepy.API, html_tweets: Union[List[Tweet], List[str]]) \
        -> List[Tweet]:
    """Get a list of Tweets or id's and download the corresponding tweets from
    the official Twitter API.

    :param api: Tweepy API object (created with setup_tweepy_api()).
    :param html_tweets: The tweets, crawled by the advanced search or their ids
    :return: List[Tweet] : Returns a list of the crawled api tweets
    """

    # if the list is empty, return an empty list
    if len(html_tweets) == 0:
        return []

    # If the list is filled with tweets, extract their id's
    if type(html_tweets[0]) is Tweet:
        id_list = _get_ids_of_tweets(html_tweets)
    else:
        id_list = html_tweets

    # Iterate through the id_batches, size = 100, and download from the API
    tweets = []
    for id_batch in _make_id_batches(id_list):
        tweets.extend(api.statuses_lookup(id_batch, tweet_mode='extended'))

    return tweets


def _get_ids_of_tweets(html_tweets: List[Tweet]) -> List[str]:
    result = []
    for tweet in html_tweets:
        result.append(tweet.id)
    return result


def _make_id_batches(tweet_ids: List[str], batch_size: int = 100) \
        -> Iterator[List[Tweet]]:
    id_batch = []
    for tweet_id in tweet_ids:
        if len(id_batch) < batch_size:
            id_batch.append(tweet_id)
        if len(id_batch) == batch_size:
            yield id_batch
            id_batch = []
    yield id_batch


if __name__ == '__main__':
    tweet_ids = ['1129802150018551808']

    config = init_nasty()
    api = setup_tweepy_api(config)
    tweet_list = download_api_tweets_from_html_tweets(api, tweet_ids)

    from pprint import pprint
    for tweet in tweet_list:
        pprint(tweet._json)
