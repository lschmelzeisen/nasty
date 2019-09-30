import gzip
import json
from datetime import date, datetime
from logging import getLogger
from multiprocessing import Pool
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple
from uuid import uuid4

import nasty
from nasty.old.advanced_search import perform_advanced_search
from nasty.util.consts import NASTY_DATE_TIME_FORMAT
from nasty.util.json import JsonSerializedException
from nasty.util.time import daterange, yyyy_mm_dd_date


class Job:
    def __init__(self, id_: str, keyword: str, date_: date, lang: str):
        self.id = id_
        self.keyword = keyword
        self.date = date_
        self.lang = lang

    def __repr__(self):
        return type(self).__name__ + repr(self.to_json())

    def to_json(self) -> Dict:
        return {
            'id': self.id,
            'keyword': self.keyword,
            'date': self.date.isoformat(),
            'lang': self.lang,
        }

    @classmethod
    def from_json(cls, obj: Dict) -> 'Job':
        return cls(id_=obj['id'],
                   keyword=obj['keyword'],
                   date_=yyyy_mm_dd_date(obj['date']),
                   lang=obj['lang'])


def build_jobs(keywords: Iterable[str],
               start_date: date,
               end_date: date,
               lang: str) -> Iterable[Job]:
    for date_ in daterange(start_date, end_date):
        for keyword in keywords:
            yield Job(uuid4().hex, keyword, date_, lang)


def write_jobs(jobs: Iterable[Job], file: Path) -> None:
    logger = getLogger(nasty.__name__)
    logger.debug('Writing jobs to "{}".'.format(file))

    with file.open('w', encoding='UTF-8') as fout:
        for job in jobs:
            json.dump(job.to_json(), fout)
            fout.write('\n')


def read_jobs(file: Path) -> Iterable[Job]:
    logger = getLogger(nasty.__name__)
    logger.debug('Reading jobs from "{}".'.format(file))

    with file.open('r', encoding='UTF-8') as fin:
        for line in fin:
            yield Job.from_json(json.loads(line))


class JobMeta:
    def __init__(self,
                 job: Job,
                 completed_at: Optional[datetime] = None,
                 exceptions: Optional[List[JsonSerializedException]] = None):
        self.job = job
        self.completed_at = completed_at
        self.exceptions = exceptions or []

    def __repr__(self):
        return type(self).__name__ + repr(self.to_json())

    def to_json(self) -> Dict:
        return {
            'job': self.job.to_json(),
            'completed-at': (self.completed_at.strftime(NASTY_DATE_TIME_FORMAT)
                             if self.completed_at else None),
            'exceptions': [e.to_json() for e in self.exceptions],
        }

    @classmethod
    def from_json(cls, obj: Dict) -> 'JobMeta':
        return cls(job=Job.from_json(obj['job']),
                   completed_at=(datetime.strptime(obj['completed_at'],
                                                   NASTY_DATE_TIME_FORMAT)
                                 if obj['completed-at'] else None),
                   exceptions=[JsonSerializedException.from_json(e)
                               for e in obj['exceptions']])


def _run_job(args: Tuple[Path, Job]) -> None:
    out_directory, job = args

    logger = getLogger(nasty.__name__)
    logger.debug('Running job {}.'.format(job))

    meta_file = out_directory / '{}.meta.json'.format(job.id)
    data_file = out_directory / '{}.data.jsonl.gz'.format(job.id)

    if meta_file.exists():
        logger.debug('  Loading JobMeta from previously created meta file.')
        with meta_file.open('r', encoding='UTF-8') as fin:
            meta = JobMeta.from_json(json.load(fin))
    else:
        meta = JobMeta(job=job)

    if meta.completed_at:
        logger.debug('  Job marked as already completed at "{}".'
                     .format(meta.completed_at.strftime(NASTY_DATE_TIME_FORMAT)))
        return

    if meta.exceptions:
        logger.debug('  Job failed previously.')

    if data_file.exists():
        logger.debug('  Deleting previously created data file because job did '
                     'not complete.')
        data_file.unlink()

    tweets = []
    try:
        tweets = perform_advanced_search(job.keyword, job.date, job.lang)
        meta.completed_at = datetime.now()
    except Exception as e:
        logger.exception('  Job failed with exception.')
        meta.exceptions.append(JsonSerializedException.from_exception(e))

    with gzip.open(data_file, 'wt', encoding='UTF-8') as fout:
        for tweet in tweets:
            json.dump(tweet.to_json(), fout)
            fout.write('\n')

    with meta_file.open('w', encoding='UTF-8') as fout:
        json.dump(meta.to_json(), fout, indent=2)


def run_jobs(jobs: Iterable[Job], num_processes: int = 1,
             out_directory: Path = Path('out')) -> None:
    Path.mkdir(out_directory, exist_ok=True, parents=True)

    with Pool(processes=num_processes) as pool:
        pool.map(_run_job, ((out_directory, job) for job in jobs))
