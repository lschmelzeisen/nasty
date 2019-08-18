import argparse
import sys
from argparse import ArgumentParser, Namespace as ArgumentNamespace
from typing import List

from nasty.generator import generate_jobs
from nasty.worker import run


def main(argv: List[str]):
    args = load_args(argv)

    generate_jobs()
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


if __name__ == '__main__':
    main(sys.argv[1:])
