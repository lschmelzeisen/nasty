import json
from datetime import date
from pathlib import Path
from typing import Dict, Iterable
from uuid import UUID, uuid4

from logging import getLogger
import nasty
from nasty.util.time import daterange, yyyy_mm_dd_date


class Job:
    def __init__(self, id_: UUID, keyword: str, date_: date, lang: str):
        self.id = id_
        self.keyword = keyword
        self.date = date_
        self.lang = lang

    def to_json(self) -> Dict:
        return {
            'id': self.id.hex,
            'keyword': self.keyword,
            'date': self.date.isoformat(),
            'lang': self.lang,
        }

    @classmethod
    def from_json(cls, obj: Dict) -> 'Job':
        return cls(id_=UUID(hex=obj['id']),
                   keyword=obj['keyword'],
                   date_=yyyy_mm_dd_date(obj['date']),
                   lang=obj['lang'])


def build_jobs(keywords: Iterable[str],
               start_date: date,
               end_date: date,
               lang: str) -> Iterable[Job]:
    for date_ in daterange(start_date, end_date):
        for keyword in keywords:
            yield Job(uuid4(), keyword, date_, lang)


def write_jobs(jobs: Iterable[Job], file: Path) -> None:
    logger = getLogger(nasty.__name__)
    logger.debug('Writing jobs to "{}".'.format(file))

    with file.open('w', encoding='UTF-8') as fout:
        for job in jobs:
            fout.write(json.dumps(job.to_json()) + '\n')


def read_jobs(file: Path) -> Iterable[Job]:
    logger = getLogger(nasty.__name__)
    logger.debug('Reading jobs from "{}".'.format(file))

    with file.open('r', encoding='UTF-8') as fin:
        for line in fin:
            yield Job.from_json(json.loads(line))
