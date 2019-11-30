from argparse import ArgumentTypeError
from datetime import date, datetime, timedelta

from typing import Iterable


# Adapted from https://stackoverflow.com/a/25470943/211404
def yyyy_mm_dd_date(string: str) -> date:
    try:
        return datetime.strptime(string, '%Y-%m-%d').date()
    except ValueError:
        raise ArgumentTypeError('Can not parse date: "{}". Make sure it is in '
                                'YYYY-MM-DD format.'.format(string))


# Adapted from: https://stackoverflow.com/a/1060352/211404
def daterange(start_date: date, end_date: date) -> Iterable[date]:
    if start_date > end_date:
        raise ValueError('End date {} before start date {}.'.format(start_date,
                                                                    end_date))

    current_date = start_date
    delta = timedelta(days=1)
    while current_date <= end_date:
        yield current_date
        current_date += delta
