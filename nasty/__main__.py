import argparse
import json
import sys
from argparse import ArgumentParser, Namespace as ArgumentNamespace
from pathlib import Path
from typing import Dict, List

from nasty.generator import generate_jobs
from nasty.worker import run


def main(argv: List[str]):
    source_folder = Path(__file__).parent.parent
    print(source_folder)

    args = load_args(argv)

    config = load_config(source_folder / 'config.json')
    from pprint import pprint
    pprint(config)

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

    args = argparser.parse_args(argv)

    return args


def load_config(path: Path) -> Dict:
    if not path.exists():
        print('Could not find config file in "{}".'.format(path))
        sys.exit()

    with path.open(encoding='UTF-8') as fin:
        config = json.load(fin)

    return config


if __name__ == '__main__':
    main(sys.argv[1:])
