import json
import toml
from typing import List, Iterator
from nasty.tweet import Tweet

import tweepy

# Authentication through a config toml file.
with open("config_api_keys.toml", "r") as KEYS:
    credentials = toml.loads(KEYS.read())
    CONSUMER_KEY = credentials['CONSUMER_KEY']
    CONSUMER_SECRET = credentials['CONSUMER_SECRET']
    ACCESS_TOKEN = credentials['ACCESS_TOKEN']
    ACCESS_TOKEN_SECRET = credentials['ACCESS_TOKEN_SECRET']
tweet_counter = 0

AUTH = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
AUTH.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)

API = tweepy.API(AUTH)


def get_ids_of_tweets(html_tweets: List[Tweet]) -> List[str]:
    result = []
    for tweet in html_tweets:
        result.append(tweet.id)
    return result


def make_id_batches(tweet_ids: List[str], batch_size: int = 100) \
        -> Iterator[List[Tweet]]:
    id_batch = []
    for tweet_id in tweet_ids:
        if len(id_batch) < batch_size:
            id_batch.append(tweet_id)
        if len(id_batch) == batch_size:
            yield id_batch
            id_batch = []
    yield id_batch


def download_api_tweets_from_html_tweets(html_tweets: List[Tweet] or List[str])\
        -> List[Tweet]:
    """
    Get a list of Tweets or id's and download the corresponding tweets from the
    official Twitter API.

    :param html_tweets: The tweets, crawled by the advanced search or their ids
    :return: List[Tweet] : Returns a list of the crawled api tweets
    """
    # if the list is empty, return an empty list
    if len(html_tweets) == 0:
        return []

    # If the list is filled with tweets, extract their id's
    if type(html_tweets[0]) is Tweet:
        id_list = get_ids_of_tweets(html_tweets)
    else:
        id_list = html_tweets

    # Iterate through the id_batches, size = 100, and download from the API
    tweets = []
    for id_batch in make_id_batches(id_list):
        tweets.extend(API.statuses_lookup(id_batch, tweet_mode='extended'))

    return tweets


if __name__ == '__main__':
    TWEET_IDS = ["1129802150018551808"]
    tweet_list = download_api_tweets_from_html_tweets(TWEET_IDS)
    print(tweet_list)
