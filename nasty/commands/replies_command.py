from argparse import ArgumentParser
from typing import List

from nasty.commands.timeline_command import TimelineCommand
from nasty.retrieval.replies import Replies


class RepliesCommand(TimelineCommand):
    @classmethod
    def command(cls) -> str:
        return 'replies'

    @classmethod
    def aliases(cls) -> List[str]:
        return ['r']

    @classmethod
    def description(cls) -> str:
        return 'Retrieve all directly replying Tweets to a Tweet.'

    @classmethod
    def config_argparser(cls, argparser: ArgumentParser) -> None:
        g = argparser.add_argument_group(
            'Replies Arguments', 'Control to which Tweet replies are '
                                 'retrieved.')
        g.add_argument('-t', '--tweet-id', metavar='<ID>', type=str,
                       required=True, help='ID of the Tweet to retrieve '
                                           'replies for (required).')

        cls._config_operational_arguments(argparser)

    def run(self) -> None:
        self._parse_operational_arguments()

        replies = Replies(self._args.tweet_id, self._args.max_tweets,
                          self._args.batch_size)

        self._print_results(replies)
