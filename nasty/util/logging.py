import logging
from logging import getLogger

import tweepy
import urllib3
import oauthlib
import requests_oauthlib


def setup_logging(level: str):
    numeric_level = getattr(logging, level)

    logging.basicConfig(
        format='{asctime} {levelname}({name}): {message}',
        style='{',
        level=numeric_level)

    # Reduce log spam from urllib3 depending on own log level.
    if numeric_level <= logging.DEBUG:
        getLogger(urllib3.__name__).setLevel(logging.INFO)
        getLogger(tweepy.__name__).setLevel(logging.INFO)
        getLogger(oauthlib.__name__).setLevel(logging.INFO)
        getLogger(requests_oauthlib.__name__).setLevel(logging.INFO)
    else:
        getLogger(urllib3.__name__).setLevel(logging.WARN)
        getLogger(tweepy.__name__).setLevel(logging.WARN)
        getLogger(oauthlib.__name__).setLevel(logging.WARN)
        getLogger(requests_oauthlib.__name__).setLevel(logging.WARN)
