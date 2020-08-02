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
from time import sleep
from typing import Iterable, Mapping, Optional, cast

import tweepy
from more_itertools import chunked

from nasty._settings import NastySettings, TwitterApiSettings

from ..tweet.tweet import Tweet, TweetId

logger = getLogger(__name__)


def _make_tweepy_api(settings: TwitterApiSettings) -> tweepy.API:
    if settings.consumer_api_key is None or settings.consumer_api_secret is None:
        raise ValueError(
            "To use this you need to create a configuration file with your Twitter API "
            "keys. Copy file config-example.nasty.toml in the nasty source folder "
            "to ${{XDG_CONFIG_HOME}}/{} and fill out the respective values.".format(
                NastySettings.Config.search_path
            )
        )

    tweepy_auth: tweepy.auth.AuthHandler
    if settings.access_token is not None and settings.access_token_secret is not None:
        tweepy_auth = tweepy.OAuthHandler(
            settings.consumer_api_key.get_secret_value(),
            settings.consumer_api_secret.get_secret_value(),
        )
        tweepy_auth.set_access_token(
            settings.access_token.get_secret_value(),
            settings.access_token_secret.get_secret_value(),
        )
    else:
        tweepy_auth = tweepy.AppAuthHandler(
            settings.consumer_api_key.get_secret_value(),
            settings.consumer_api_secret.get_secret_value(),
        )
    return tweepy.API(tweepy_auth, parser=tweepy.parsers.JSONParser())


STATUSES_LOOKUP_CHUNK_SIZE = 100
CHUNK_LOOKUPS_SINCE_LAST_RATE_LIMIT_ERROR = 0
TWEEPY_API: Optional[tweepy.API] = None


def statuses_lookup(
    tweet_ids: Iterable[TweetId], twitter_api_settings: TwitterApiSettings
) -> Iterable[Optional[Tweet]]:
    global CHUNK_LOOKUPS_SINCE_LAST_RATE_LIMIT_ERROR
    global TWEEPY_API

    if TWEEPY_API is None:
        TWEEPY_API = _make_tweepy_api(twitter_api_settings)

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
