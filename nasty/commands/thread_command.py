from argparse import ArgumentParser
from typing import List

from nasty.commands.timeline_command import TimelineCommand


class ThreadCommand(TimelineCommand):
    @classmethod
    def command(cls) -> str:
        return 'thread'

    @classmethod
    def aliases(cls) -> List[str]:
        return ['t']

    @classmethod
    def description(cls) -> str:
        return 'Retrieve all Tweets threaded under a Tweet.'

    @classmethod
    def config_argparser(cls, argparser: ArgumentParser) -> None:
        g = argparser.add_argument_group(
            'Thread Arguments', 'Control to which Tweet threaded Tweets are '
                                'retrieved.')
        g.add_argument('-t', '--tweet-id', metavar='<ID>', type=str,
                       required=True, help='ID of the Tweet to retrieve '
                                           'threaded Tweets for (required).')

        cls.config_operational_arguments(argparser)

    def run(self) -> None:
        self.parse_operational_arguments()
