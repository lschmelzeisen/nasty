import argparse
import logging
import sys
from argparse import ArgumentParser, Namespace as ArgumentNamespace
from logging import getLogger
from typing import List, Tuple

import nasty
from nasty.old_v2.commands.command import Command
from nasty.old_v2.commands import RepliesCommand
from nasty.old_v2.commands import SearchCommand
from nasty.old_v2.commands import ThreadCommand
from nasty._util.argparse import SingleMetavarHelpFormatter
from nasty._util.logging_ import setup_logging


def main(argv: List[str]):
    args, command = _load_args(argv)

    numeric_log_level = getattr(logging, args.log_level)
    setup_logging(numeric_log_level)

    logger = getLogger(nasty.__name__)
    logger.debug('Raw arguments: {}'.format(argv))
    logger.debug('Parsed arguments: {}'.format(vars(args)))
    logger.debug('Parsed command: {}.{}'.format(command.__module__,
                                                command.__name__))

    command(args).run()


def _load_args(argv: List[str]) -> Tuple[ArgumentNamespace, Command.__class__]:
    argparser = ArgumentParser(prog='nasty',
                               description='NASTY - NASTY Advanced Search '
                                           'Tweet Yielder, a Twitter crawler.',
                               add_help=False,
                               formatter_class=SingleMetavarHelpFormatter)

    subparsers = argparser.add_subparsers(title='command', metavar='<COMMAND>')
    subparsers.required = True

    for subcommand in [SearchCommand, RepliesCommand, ThreadCommand]:
        subparser = subparsers.add_parser(
            subcommand.command(),
            aliases=subcommand.aliases(),
            help=subcommand.description(),
            description=subcommand.description(),
            add_help=False,
            formatter_class=SingleMetavarHelpFormatter)
        subparser.set_defaults(command=subcommand)
        subcommand.config_argparser(subparser)
        _config_general_args(subparser)

    _config_general_args(argparser)

    args = argparser.parse_args(argv)

    return args, args.command


def _config_general_args(argparser: ArgumentParser) -> None:
    g = argparser.add_argument_group('General Arguments')

    # The following line & the add_help=False above is to be able to customize
    # the help message. See: https://stackoverflow.com/a/35848313/211404
    g.add_argument('-h', '--help', action='help',
                   default=argparse.SUPPRESS,
                   help='Show this help message and exit.')

    g.add_argument('-v', '--version', action='version',
                   version='%(prog)s development version',
                   help='Show program\'s version number and exit.')

    g.add_argument('--log-level', metavar='<LEVEL>', type=str,
                   choices=['DEBUG', 'INFO', 'WARN', 'ERROR'], default='INFO',
                   help='Logging level (DEBUG, INFO, WARN, ERROR.)')


if __name__ == '__main__':
    main(sys.argv[1:])
