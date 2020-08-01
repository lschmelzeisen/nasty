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


def _get_key(name: str) -> Optional[str]:
    key = getenv(name)
    # Check if environment variable is not set or set to default
    return key if (key is not None and " " not in key) else None


def _make_tweepy_api() -> tweepy.API:
    consumer_api_key = _get_key("NASTY_CONSUMER_API_KEY")
    consumer_api_secret = _get_key("NASTY_CONSUMER_API_SECRET")
    access_token = _get_key("NASTY_ACCESS_TOKEN")
    access_token_secret = _get_key("NASTY_ACCESS_TOKEN_SECRET")
    if consumer_api_key is None or consumer_api_secret is None:
        raise ValueError(
            "To use this you need to define environment variables with your Twitter "
            "API keys. Set file config.example.sh in the nasty source folder and "
            "source it into your environment, e.g., via `source config.example.sh`."
        )

    tweepy_auth: tweepy.auth.AuthHandler
    if access_token is not None and access_token_secret is not None:
        tweepy_auth = tweepy.OAuthHandler(consumer_api_key, consumer_api_secret)
        tweepy_auth.set_access_token(access_token, access_token_secret)
    else:
        tweepy_auth = tweepy.AppAuthHandler(consumer_api_key, consumer_api_secret)
    return tweepy.API(tweepy_auth, parser=tweepy.parsers.JSONParser())


STATUSES_LOOKUP_CHUNK_SIZE = 100
CHUNK_LOOKUPS_SINCE_LAST_RATE_LIMIT_ERROR = 0
TWEEPY_API: Optional[tweepy.API] = None


def statuses_lookup(tweet_ids: Iterable[TweetId]) -> Iterable[Optional[Tweet]]:
    global CHUNK_LOOKUPS_SINCE_LAST_RATE_LIMIT_ERROR
    global TWEEPY_API

    if TWEEPY_API is None:
        TWEEPY_API = _make_tweepy_api()

    for tweet_ids_chunk in chunked(tweet_ids, STATUSES_LOOKUP_CHUNK_SIZE):
        num_retries = 0
        while True:
            exception: Exception
            try:
                tweets_chunk = cast(
                    Mapping[str, Mapping[str, Optional[Mapping[str, object]]]],
                    TWEEPY_API.statuses_lookup(
                        tweet_ids_chunk,
                        include_entities=True,
                        map_=True,
                        tweet_mode="extended",
                    ),
                )["id"]
                CHUNK_LOOKUPS_SINCE_LAST_RATE_LIMIT_ERROR += 1
                for tweet_id in tweet_ids_chunk:
                    tweet_json = tweets_chunk[tweet_id]
                    if tweet_json is not None:
                        yield Tweet(tweet_json)
                    else:
                        yield None
                break

            except tweepy.RateLimitError as e:
                logger.debug(
                    "Chunk lookups since last rate limit error: {}.".format(
                        CHUNK_LOOKUPS_SINCE_LAST_RATE_LIMIT_ERROR
                    )
                )
                CHUNK_LOOKUPS_SINCE_LAST_RATE_LIMIT_ERROR = 0

                logger.info("Hit rate limit error. Sleeping for 15mins...")
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
