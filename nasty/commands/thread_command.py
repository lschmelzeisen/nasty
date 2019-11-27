from argparse import ArgumentParser
from typing import List

from nasty.commands.timeline_command import TimelineCommand
from nasty.retrieval.thread import Thread
from nasty.retrieval.timeline import Timeline


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
    def _config_retrieval_args(cls, argparser: ArgumentParser) -> None:
        g = argparser.add_argument_group(
            'Thread Arguments', 'Control to which Tweet threaded Tweets are '
                                'retrieved.')
        g.add_argument('-t', '--tweet-id', metavar='<ID>', type=str,
                       required=True, help='ID of the Tweet to retrieve '
                                           'threaded Tweets for (required).')

    def setup_retrieval(self) -> Timeline:
        return Thread(self._args.tweet_id,
                      self._args.max_tweets,
                      self._args.batch_size)
