#
# Copyright 2019 Lukas Schmelzeisen
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

from logging import getLogger
from typing import Dict, List, Union

import nasty
import tweepy
from nasty._util.misc import chunked
from nasty.old.init import init_nasty
from nasty.old.tweet import Tweet


def setup_tweepy_api(config: Dict) -> tweepy.API:
    auth = tweepy.OAuthHandler(
        config["twitter_api"]["consumer_key"],
        config["twitter_api"]["consumer_key_secret"],
    )
    auth.set_access_token(
        config["twitter_api"]["access_token"],
        config["twitter_api"]["access_token_secret"],
    )

    api = tweepy.API(auth)
    return api


def download_api_tweets(
    api: tweepy.API, tweets: List[Union[str, Tweet]]
) -> List[tweepy.Status]:
    """Downloads Tweets via the official Twitter API.

    :param api: Tweet API object, created with setup_tweepy_api().
    :param tweets: A list of either Tweet IDs to download or Tweet objects whose
        IDs will be extracted from them.
    :return: List of downloaded Tweets.
    """

    logger = getLogger(nasty.__name__)
    logger.debug("Download {:d} tweets from Twitter API.".format(len(tweets)))

    tweet_ids = [tweet.id if isinstance(tweet, Tweet) else tweet for tweet in tweets]

    tweets = []
    for i, tweet_id_batch in enumerate(chunked(100, tweet_ids)):
        logger.debug("  Batch {:d} of IDs: {}".format(i, tweet_id_batch))
        tweets.extend(api.statuses_lookup(tweet_id_batch, tweet_mode="extended"))

    return tweets


if __name__ == "__main__":
    tweet_ids = ["1129802150018551808", "1147178639298973696", "899787401769308160"]

    config = init_nasty()
    api = setup_tweepy_api(config)
    tweet_list = download_api_tweets(api, tweet_ids)

    from pprint import pprint

    for tweet in tweet_list:
        pprint(tweet._json)
