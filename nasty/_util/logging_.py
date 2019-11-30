import logging
from logging import getLogger

import urllib3


def setup_logging(level: int) -> None:
    logging.basicConfig(
        format='%(asctime)s %(levelname)1.1s [ %(name)-31s ] %(message)s',
        level=level)

    # Reduce log spam from urllib3 depending on own log level.
    if level <= logging.DEBUG:
        getLogger(urllib3.__name__).setLevel(logging.INFO)
    else:
        getLogger(urllib3.__name__).setLevel(logging.WARN)
