import gzip
import json
import os
from typing import List

import tweepy

# Authentication
CONSUMER_KEY = "hniLShzTr9Lcp9db4Lrb6Vhxq"
CONSUMER_SECRET = "pcswbLNZ6WxjC0UQKXG7QLCWLgjWcQr8FOuKNWJwevdbywecc4"
ACCESS_TOKEN = "1117712996795658241-5VRKHLKRRBF7Mb1h0UAqWiJT42AI3m"
ACCESS_TOKEN_SECRET = "z3lCUT0lCBZ8Yv3FV6dtWhPmad3lSpjwQYZHJdd86MPBn"
tweet_counter = 0

AUTH = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
AUTH.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)

API = tweepy.API(AUTH)


def get_ids(read_from: str) -> List[str]:
    """
    Here we read the ids out of a file and return a list of them.
    :param read_from:
    :return: List of Tweets IDs (str)
    """
    id_list = list()
    with gzip.open(read_from, "rt") as fp:
        for line in fp:
            data = json.loads(line)
            id_list.append(data["id_str"])
    return id_list


def load(read_from: str, save_to: str) -> None:
    """
    Reads all ids from a file, downloads them in packs of 100 and
    saves the API data into a file.

    :param read_from: The file to read from.
    :param save_to: The file to save the API._json to
    :return:
    """
    id_list = get_ids(read_from)
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
    if "/" in save_to:
        os.makedirs(os.path.dirname(save_to), exist_ok=True)
    with gzip.open(save_to, "wt") as fp:
        for tweet in tweets:
            fp.write(json.dumps(tweet._json))
            fp.write("\n")


if __name__ == '__main__':
    TWEET_IDS = ["1129802150018551808"]
    TWEETS = API.statuses_lookup(TWEET_IDS, tweet_mode='extended')
    with open("data/SingleID.json", "wt") as single:
        for item in TWEETS:
            single.write(json.dumps(item._json))
            single.write("\n")
    # load("out/ape-2019-5-20.json.gz", "out/APIape-2019-5-20.json.gz")
