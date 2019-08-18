from argparse import ArgumentTypeError
from datetime import date, datetime


# Adapted from https://stackoverflow.com/a/25470943/211404
def yyyy_mm_dd_date(string: str) -> date:
    try:
        return datetime.strptime(string, '%Y-%m-%d').date()
    except ValueError:
        raise ArgumentTypeError('Can not parse date: "{}". Make sure it is in '
                                'YYYY-MM-DD format.'.format(string))
