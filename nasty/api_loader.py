import json
import toml
from typing import List
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


def get_ids(html_tweets: List[Tweet]) -> List[str]:
    result = []
    for tweet in html_tweets:
        result.append(tweet.id)
    return result


def load(html_tweets: List[Tweet]) -> List[Tweet]:
    """
    Reads all ids from a list of tweets, downloads them in packs of 100,
    using the ID search functionality of the API, and returns
    a list containing the crawled tweets.

    :param html_tweets: The tweets, crawled by the advanced search, from wich
                        we extract the ID's.
    :return: List[Tweet] : Returns a list of the crawled api tweets, which
                            futhermore can be compared to the .
    """

    id_list = get_ids(html_tweets)
    tweets = []
    for stack in range(divmod(len(id_list), 100)[0]):
        send = list()
        i = 0
        while i < 100:
            send.append(id_list[i + 100 * stack])
            i += 1
            print(i + 100 * stack)
        tweets.extend(API.statuses_lookup(send, tweet_mode='extended'))

    send = list()
    stack = divmod(len(id_list), 100)[0]
    i = 0
    while i < divmod(len(id_list), 100)[1]:
        send.append(id_list[i + 100 * stack])
        i += 1
        print(i + 100 * stack)
    tweets.extend(API.statuses_lookup(send, tweet_mode='extended'))
    # Got an error, if we used data in the current folder
    # "example.json.gz" and not "data/example.json.gz"
    return tweets


if __name__ == '__main__':
    TWEET_IDS = ["1129802150018551808"]
    TWEETS = API.statuses_lookup(TWEET_IDS, tweet_mode='extended')
    with open("data/SingleID.json", "wt") as single:
        for item in TWEETS:
            single.write(json.dumps(item._json))
            single.write("\n")
    # load("out/ape-2019-5-20.json.gz", "out/APIape-2019-5-20.json.gz")
