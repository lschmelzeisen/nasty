from argparse import ArgumentParser
from typing import List

from nasty.commands.timeline_command import TimelineCommand
from nasty.retrieval.search import Search
from nasty.util.time import yyyy_mm_dd_date


class SearchCommand(TimelineCommand):
    @classmethod
    def command(cls) -> str:
        return 'search'

    @classmethod
    def aliases(cls) -> List[str]:
        return ['s']

    @classmethod
    def description(cls) -> str:
        return 'Retrieve Tweets using the Twitter Advanced Search.'

    @classmethod
    def config_argparser(cls, argparser: ArgumentParser) -> None:
        g = argparser.add_argument_group(
            'Search Arguments', 'Control what kind of Tweets are searched.')
        g.add_argument('-q', '--query', metavar='<QUERY>', type=str,
                       required=True, help='Search string (required).')
        g.add_argument('-s', '--since', metavar='<DATE>', type=yyyy_mm_dd_date,
                       help='Earliest date for Tweets (inclusive).')
        g.add_argument('-u', '--until', metavar='<DATE>', type=yyyy_mm_dd_date,
                       help='Latest date for Tweets (exclusive).')
        g.add_argument('-f', '--filter', metavar='<FILTER>',
                       type=Search.Query.Filter.__getitem__,
                       default=Search.Query.Filter.DEFAULT_FILTER,
                       help='Sorting/filtering of Tweets (TOP, LATEST, PHOTOS, '
                            'VIDEOS). Defaults to "TOP".')
        g.add_argument('-l', '--lang', metavar='<LANG>', default='en',
                       help='Two-letter language code for Tweets. Defaults to '
                            '"en".')

        cls._config_operational_arguments(argparser)

    def run(self) -> None:
        self._parse_operational_arguments()

        query = Search.Query(self._args.query, self._args.since,
                             self._args.until, self._args.filter,
                             self._args.lang)
        search = Search(query, self._args.max_tweets, self._args.batch_size)

        self._print_results(search)
