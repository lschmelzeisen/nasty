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

import argparse
import logging
import sys
from argparse import ArgumentParser
from logging import getLogger
from typing import Optional, Sequence, Tuple, Type

import nasty

from .._util.argparse_ import SingleMetavarHelpFormatter
from .._util.logging_ import setup_logging
from ._batch_command import _BatchCommand
from ._command import _Command
from ._idify_command import _IdifyCommand
from ._replies_command import _RepliesCommand
from ._search_command import _SearchCommand
from ._thread_command import _ThreadCommand
from ._unidify_command import _UnidifyCommand

logger = getLogger(__name__)


def main(argv: Optional[Sequence[str]] = None) -> None:
    if argv is None:  # pragma: no cover
        argv = sys.argv[1:]

    args, command = _load_args(argv)

    numeric_log_level = getattr(logging, args.log_level)
    setup_logging(numeric_log_level)

    logger.debug("NASTY version: {}".format(nasty.__version__))
    logger.debug("Raw arguments: {}".format(argv))
    logger.debug("Parsed arguments: {}".format(vars(args)))
    logger.debug(
        "Parsed command: {}.{}".format(type(command).__module__, type(command).__name__)
    )

    command.run()


def _load_args(argv: Sequence[str]) -> Tuple[argparse.Namespace, _Command]:
    command_types: Sequence[Type[_Command]] = [
        _SearchCommand,
        _RepliesCommand,
        _ThreadCommand,
        _BatchCommand,
        _IdifyCommand,
        _UnidifyCommand,
    ]

    argparser = ArgumentParser(
        prog="nasty",
        usage=(
            "nasty [-h] [-v] ["
            + "|".join(command_type.command() for command_type in command_types)
            + "] ..."
        ),
        description="NASTY Advanced Search Tweet Yielder.",
        add_help=False,
        formatter_class=SingleMetavarHelpFormatter,
    )

    subparsers = argparser.add_subparsers(
        title="Commands",
        description="The following commands (and abbreviations) are available, each "
        "supporting the help option. For example, try out `nasty search --help`.",
        metavar="<COMMAND>",
        prog="nasty",
    )
    subparsers.required = True

    subparser_by_command_type = {}
    for command_type in command_types:
        subparser = subparsers.add_parser(
            command_type.command(),
            aliases=command_type.aliases(),
            help=command_type.description(),
            description=command_type.description(),
            add_help=False,
            formatter_class=SingleMetavarHelpFormatter,
        )
        subparser.set_defaults(command=command_type)
        subparser_by_command_type[command_type] = subparser
        command_type.config_argparser(subparser)
        _config_general_args(subparser)

    _config_general_args(argparser)

    args = argparser.parse_args(argv)

    command = args.command(args)
    command.validate_arguments(subparser_by_command_type[args.command])

    return args, command


def _config_general_args(argparser: ArgumentParser) -> None:
    g = argparser.add_argument_group("General Arguments")

    # The following line & the add_help=False above is to be able to customize
    # the help message. See: https://stackoverflow.com/a/35848313/211404
    g.add_argument(
        "-h",
        "--help",
        action="help",
        default=argparse.SUPPRESS,
        help="Show this help message and exit.",
    )

    g.add_argument(
        "-v",
        "--version",
        action="version",
        version="%(prog)s " + nasty.__version__,
        help="Show program's version number and exit.",
    )

    g.add_argument(
        "--log-level",
        metavar="<LEVEL>",
        type=str,
        choices=["DEBUG", "INFO", "WARN", "ERROR"],
        default="INFO",
        help="Logging level (DEBUG, INFO, WARN, ERROR.)",
    )
