#
# Copyright 2019-2020 Lukas Schmelzeisen
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

from argparse import ArgumentTypeError
from datetime import date, datetime, timedelta
from typing import Iterable


# Adapted from https://stackoverflow.com/a/25470943/211404
def yyyy_mm_dd_date(string: str) -> date:
    try:
        return datetime.strptime(string, "%Y-%m-%d").date()
    except ValueError:
        raise ArgumentTypeError(
            'Can not parse date: "{}". Make sure it is in '
            "YYYY-MM-DD format.".format(string)
        )


# Adapted from: https://stackoverflow.com/a/1060352/211404
def daterange(start_date: date, end_date: date) -> Iterable[date]:
    if start_date > end_date:
        raise ValueError(
            "End date {} before start date {}.".format(start_date, end_date)
        )

    current_date = start_date
    delta = timedelta(days=1)
    while current_date <= end_date:
        yield current_date
        current_date += delta
