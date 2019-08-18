import json
from datetime import date
from pathlib import Path
from typing import Dict, Iterable

from nasty.util.time import daterange


class Job:
    def __init__(self, keyword: str, date_: date, lang: str):
        self.keyword = keyword
        self.date = date_
        self.lang = lang

    def to_json(self) -> Dict:
        return {
            'keyword': self.keyword,
            'date': self.date.isoformat(),
            'lang': self.lang,
        }

    @classmethod
    def from_json(cls, obj: Dict) -> 'Job':
        return cls(obj['keyword'], obj['date'], obj['lang'])


def build_jobs(keywords: Iterable[str],
               start_date: date,
               end_date: date,
               lang: str) -> Iterable[Job]:
    for date_ in daterange(start_date, end_date):
        for keyword in keywords:
            yield Job(keyword, date_, lang)


def write_jobs(jobs: Iterable[Job], file: Path) -> None:
    with file.open('w', encoding='UTF-8') as fout:
        for job in jobs:
            fout.write(json.dumps(job.to_json()))
            fout.write('\n')
