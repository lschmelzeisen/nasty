import argparse
import sys
from argparse import ArgumentParser, Namespace as ArgumentNamespace
from logging import getLogger
from typing import List

import nasty
from nasty.init import get_source_folder, init_nasty
from nasty.old.jobs import build_jobs, read_jobs, run_jobs, write_jobs
from nasty.util.time import yyyy_mm_dd_date


def main(argv: List[str]):
    config = init_nasty()
    args = load_args(argv)

    jobs = build_jobs(keywords=args.keywords,
                      start_date=args.time[0],
                      end_date=args.time[1],
                      lang=args.lang)
    write_jobs(jobs, get_source_folder() / 'jobs.jsonl')

    jobs = read_jobs(get_source_folder() / 'jobs.jsonl')
    run_jobs(jobs, num_processes=config['num_processes'])


def load_args(argv: List[str]) -> ArgumentNamespace:
    logger = getLogger(nasty.__name__)
    logger.debug('Raw arguments: {}'.format(argv))

    argparser = ArgumentParser(prog='nasty',
                               description='NASTY - NASTY Advanced Search '
                                           'Tweet Yielder, a Twitter crawler.',
                               add_help=False)

    # The following line & the add_help=False above is to be able to customize
    # the help message. See: https://stackoverflow.com/a/35848313/211404
    argparser.add_argument('-h', '--help', action='help',
                           default=argparse.SUPPRESS,
                           help='Show this help message and exit.')

    argparser.add_argument('-v', '--version', action='version',
                           version='%(prog)s development version',
                           help='Show program\'s version number and exit.')

    argparser.add_argument('-k', '--keywords', metavar='<KEYWORD>',
                           type=str, nargs='+', required=True, dest='keywords',
                           help='Keywords to search for.')

    argparser.add_argument('-t', '--time', metavar='<DATE>',
                           type=yyyy_mm_dd_date, nargs=2, required=True,
                           dest='time',
                           help='Time range the returned tweets need to be in.'
                                ' Date format needs to be "YYYY-MM-DD".')

    argparser.add_argument('--lang', metavar='<LANG>', type=str, dest='lang',
                           default='en', help='Twitter Language to crawl with'
                                              ' (default: "en").')

    args = argparser.parse_args(argv)
    logger.debug('Parsed arguments: {}'.format(vars(args)))

    return args


if __name__ == '__main__':
    main(sys.argv[1:])
