from argparse import ArgumentParser
from typing import Iterable, List

from nasty.commands.timeline_command import TimelineCommand
from nasty.retrieval.replies import Replies
from nasty.tweet import Tweet


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
    def _config_retrieval_arguments(cls, argparser: ArgumentParser) -> None:
        g = argparser.add_argument_group(
            'Replies Arguments', 'Control to which Tweet replies are '
                                 'retrieved.')
        g.add_argument('-t', '--tweet-id', metavar='<ID>', type=str,
                       required=True, help='ID of the Tweet to retrieve '
                                           'replies for (required).')

    def retrieval_iterable(self) -> Iterable[Tweet]:
        return Replies(self._args.tweet_id,
                       self._args.max_tweets,
                       self._args.batch_size)
