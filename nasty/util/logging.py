import logging
from logging import getLogger

import urllib3


def setup_logging(level: str) -> None:
    numeric_level = getattr(logging, level)

    logging.basicConfig(
        format='{asctime} {levelname:1.1} [ {name:14} ] {message}',
        style='{',
        level=numeric_level)

    # Reduce log spam from urllib3 depending on own log level.
    if numeric_level <= logging.DEBUG:
        getLogger(urllib3.__name__).setLevel(logging.INFO)
    else:
        getLogger(urllib3.__name__).setLevel(logging.WARN)
