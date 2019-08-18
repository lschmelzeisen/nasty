import argparse
import sys
from argparse import ArgumentParser, Namespace as ArgumentNamespace
from logging import getLogger
from pathlib import Path
from typing import Dict, List

import toml

import nasty
from nasty.generator import generate_jobs
from nasty.worker import run
from nasty.util.logging import setup_logging


def main(argv: List[str]):
    source_folder = Path(__file__).parent.parent

    args = load_args(argv)

    setup_logging(args.log_level)
    logger = getLogger(nasty.__name__)
    logger.debug('Raw arguments: {}'.format(argv))
    logger.debug('Parsed arguments: {}'.format(vars(args)))

    config = load_config(source_folder / 'config.toml')

    generate_jobs(config)
    run(4, True)


def load_args(argv: List[str]) -> ArgumentNamespace:
    argparser = ArgumentParser(prog='nasty',
                               description='NASTY - NASTY Advanced Search '
                                           'Tweet Yielder, a Twitter crawler.',
                               add_help=False)

    # The following line and the add_help=False above is to be able to customize
    # the help message. See: https://stackoverflow.com/a/35848313/211404
    argparser.add_argument('-h', '--help', action='help',
                           default=argparse.SUPPRESS,
                           help='Show this help message and exit.')

    argparser.add_argument('-v', '--version', action='version',
                           version='%(prog)s development version',
                           help='Show program\'s version number and exit.')

    argparser.add_argument('--log-level', metavar='<level>', type=str,
                           choices=['DEBUG', 'INFO', 'WARN', 'ERROR'],
                           default='INFO', dest='log_level',
                           help='Set logging level (DEBUG, INFO, WARN, ERROR).')

    args = argparser.parse_args(argv)

    return args


def load_config(path: Path) -> Dict:
    logger = getLogger(nasty.__name__)

    if not path.exists():
        logger.error('Could not find config file in "{}".'.format(path))
        sys.exit()

    logger.debug('Loading config from "{}".'.format(path))
    with path.open(encoding='UTF-8') as fin:
        config = toml.load(fin)

    logger.debug('Loaded config:')
    for line in toml.dumps(config).splitlines():
        logger.debug('  ' + line)

    return config


if __name__ == '__main__':
    main(sys.argv[1:])
