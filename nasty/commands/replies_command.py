from argparse import ArgumentParser
from typing import List

from nasty.commands.timeline_command import TimelineCommand


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

        cls.config_operational_arguments(argparser)

    def run(self) -> None:
        self.parse_operational_arguments()
