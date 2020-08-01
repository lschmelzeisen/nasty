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

import logging
from logging import getLogger

import oauthlib  # type: ignore
import requests_oauthlib  # type: ignore
import tweepy
import urllib3


def setup_logging(level: int) -> None:
    logging.basicConfig(
        format="%(asctime)s %(levelname)1.1s [ %(name)-31s ] %(message)s", level=level
    )

    # Reduce log spam from urllib3 depending on own log level.
    getLogger(oauthlib.__name__).setLevel(logging.INFO)
    getLogger(requests_oauthlib.__name__).setLevel(logging.INFO)
    getLogger(tweepy.binder.__name__).setLevel(logging.INFO)
    if level <= logging.DEBUG:
        getLogger(urllib3.__name__).setLevel(logging.INFO)
    else:
        getLogger(urllib3.__name__).setLevel(logging.WARN)
