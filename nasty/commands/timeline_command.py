import json
from abc import abstractmethod
from argparse import ArgumentParser
from typing import Iterable, List

from nasty.commands.command import Command
from nasty.tweet import Tweet


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
    @abstractmethod
    def config_argparser(cls, argparser: ArgumentParser) -> None:
        raise NotImplementedError()

    @abstractmethod
    def run(self) -> None:
        raise NotImplementedError()

    @classmethod
    def _config_operational_arguments(cls, argparser: ArgumentParser) -> None:
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

    def _parse_operational_arguments(self) -> None:
        if self._args.max_tweets == -1:
            self._args.max_tweets = None
        if self._args.batch_size == -1:
            self._args.batch_size = None

    @classmethod
    def _print_results(cls, results: Iterable[Tweet]) -> None:
        for tweet in results:
            print(json.dumps(tweet.to_json()))
