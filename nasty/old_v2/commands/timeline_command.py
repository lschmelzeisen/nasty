import argparse
import json
from abc import abstractmethod
from argparse import ArgumentParser
from typing import List

from nasty.old_v2.commands.command import Command
from nasty.retrieval.timeline import Timeline
from nasty._util.disrespect_robotstxt import disrespect_robotstxt


class TimelineCommand(Command):
    # Repeating abstractmethod definitions of base class to not trigger
    # PyCharm's inspection to implement abstract base methods.

    @classmethod
    @abstractmethod
    def command(cls) -> str:
        raise NotImplementedError()

    @classmethod
    @abstractmethod
    def aliases(cls) -> List[str]:
        raise NotImplementedError()

    @classmethod
    @abstractmethod
    def description(cls) -> str:
        raise NotImplementedError()

    @classmethod
    def config_argparser(cls, argparser: ArgumentParser) -> None:
        cls._config_retrieval_args(argparser)

        g = argparser.add_argument_group(
            'Operational Arguments', 'Control how Tweets are retrieved.')
        g.add_argument('-n', '--max-tweets', metavar='<N>', type=int,
                       default=100, help='Maximum number of tweets to '
                                         'retrieve. Set to -1 to receive as '
                                         'many as possible. Defaults to 100.')
        g.add_argument('-b', '--batch-size', metavar='<N>', type=int,
                       default=-1, help='Batch size to retrieve Tweets in. '
                                        'Set to -1 for default behavior. Only '
                                        'change when necessary.')
        g.add_argument('-d', '--disrespect-robotstxt', action='store_true',
                       help=argparse.SUPPRESS)

        g = argparser.add_argument_group('Job Arguments')
        g.add_argument('-j', '--job', action='store_true',
                       help='lel')

    @classmethod
    @abstractmethod
    def _config_retrieval_args(cls, argparser: ArgumentParser) -> None:
        raise NotImplementedError()

    def run(self) -> None:
        if self._args.max_tweets == -1:
            self._args.max_tweets = None
        if self._args.batch_size == -1:
            self._args.batch_size = None

        if self._args.job:
            print(json.dumps(self.setup_retrieval().to_job().to_json()))
        elif self._args.disrespect_robotstxt:
            self.run_retrieval_with_disrespect_robotstxt()
        else:
            self.run_retrieval()

    @abstractmethod
    def setup_retrieval(self) -> Timeline:
        raise NotImplementedError()

    @disrespect_robotstxt
    def run_retrieval_with_disrespect_robotstxt(self) -> None:
        """Wrapper for dynamic addition of @disrespect_robotstxt decorator."""
        self.run_retrieval()

    def run_retrieval(self) -> None:
        for tweet in self.setup_retrieval():
            print(json.dumps(tweet.to_json()))
