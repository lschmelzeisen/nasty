#
# Copyright 2019-2020 Lukas Schmelzeisen
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
from os import getenv
from time import sleep
from typing import Iterable, Mapping, Optional, cast

import tweepy
from more_itertools import chunked

from ..tweet.tweet import Tweet, TweetId

logger = getLogger(__name__)

STATUSES_LOOKUP_CHUNK_SIZE = 100


def statuses_lookup(tweet_ids: Iterable[TweetId]) -> Iterable[Optional[Tweet]]:
    consumer_key = getenv("NASTY_CONSUMER_KEY")
    consumer_secret = getenv("NASTY_CONSUMER_SECRET")
    if consumer_key is None or consumer_secret is None:
        raise ValueError(
            "To use this you need to define environment variables with your Twitter "
            "API keys. See file config.sh in the nasty source folder and source it "
            "into your environment, e.g., via `source config.sh`."
        )

    tweepy_auth = tweepy.AppAuthHandler(consumer_key, consumer_secret)
    tweepy_api = tweepy.API(tweepy_auth, parser=tweepy.parsers.JSONParser())

    for tweet_ids_chunk in chunked(tweet_ids, STATUSES_LOOKUP_CHUNK_SIZE):
        num_retries = 0
        while True:
            exception: Exception
            try:
                tweets_chunk = cast(
                    Mapping[str, Mapping[str, Optional[Mapping[str, object]]]],
                    tweepy_api.statuses_lookup(
                        tweet_ids_chunk,
                        include_entities=True,
                        map_=True,
                        tweet_mode="extended",
                    ),
                )["id"]
                for tweet_id in tweet_ids_chunk:
                    tweet_json = tweets_chunk[tweet_id]
                    if tweet_json is not None:
                        yield Tweet(tweet_json)
                break

            except tweepy.RateLimitError as e:
                logger.info("Hit rate limit error")
                logger.info("Sleeping for 15mins...")
                sleep(15 * 60)
                logger.info("Retrying...")
                exception = e

            except Exception as e:
                logger.exception("Exception occurred.")
                logger.info("Retrying (retry {})...".format(num_retries))
                exception = e

            num_retries += 1
            if num_retries == 3:
                logger.error("Maximum number of retries exceeded.")
                raise exception
