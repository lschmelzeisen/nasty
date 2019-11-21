import json
import lzma
import multiprocessing
from datetime import datetime
from logging import getLogger
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4

from nasty.search import Search
from nasty.util.consts import NASTY_DATE_TIME_FORMAT
from nasty.util.json import JsonSerializedException


class Job:
    def __init__(self,
                 id: str,
                 query: Search.Query,
                 max_tweets: int,
                 batch_size: Optional[int] = None,
                 completed_at: Optional[datetime] = None,
                 exception: Optional[JsonSerializedException] = None):
        self.id = id
        self.query = query
        self.max_tweets = max_tweets
        self.batch_size = batch_size
        self.completed_at = completed_at
        self.exception = exception

    @property
    def meta_file_name(self) -> Path:
        return Path('{:s}.meta.json'.format(self.id))

    @property
    def data_file_name(self) -> Path:
        return Path('{:s}.data.jsonl.xz'.format(self.id))

    def __repr__(self) -> str:
        return type(self).__name__ + repr(self.to_json())

    def __eq__(self, other: Any) -> bool:
        return (type(self) == type(other)) and (self.__dict__ == other.__dict__)

    def match(self, other: 'Job') -> bool:
        return (self.query == other.query
                and self.max_tweets == other.max_tweets
                and self.batch_size == other.batch_size)

    def to_json(self) -> Dict[str, Any]:
        obj = {}
        obj['id'] = self.id
        obj['query'] = self.query.to_json()
        obj['max_tweets'] = self.max_tweets
        obj['batch_size'] = self.batch_size

        if self.completed_at:
            obj['completed-at'] = \
                self.completed_at.strftime(NASTY_DATE_TIME_FORMAT)

        if self.exception is not None:
            obj['exception'] = self.exception.to_json()

        return obj

    @classmethod
    def from_json(cls, obj: Dict[str, Any]) -> 'Job':
        return cls(id=obj['id'],
                   query=Search.Query.from_json(obj['query']),
                   max_tweets=obj['max_tweets'],
                   batch_size=obj['batch_size'],
                   completed_at=(datetime.strptime(obj['completed-at'],
                                                   NASTY_DATE_TIME_FORMAT)
                                 if 'completed-at' in obj else None),
                   exception=(
                       JsonSerializedException.from_json(obj['exception'])
                       if 'exception' in obj else None))


class Jobs:
    def __init__(self, jobs: List[Job]):
        self._jobs = jobs

    def __eq__(self, other: Any) -> bool:
        return (type(self) == type(other)) and (self.__dict__ == other.__dict__)

    @classmethod
    def new(cls) -> 'Jobs':
        return cls([])

    def dump(self, file: Path) -> None:
        logger = getLogger(__name__)
        logger.debug('Saving jobs to file "{}".'.format(file))

        with file.open('w', encoding='UTF-8') as fout:
            for job in self._jobs:
                fout.write('{:s}\n'.format(json.dumps(job.to_json())))

    @classmethod
    def load(cls, file: Path) -> 'Jobs':
        logger = getLogger(__name__)
        logger.debug('Loading jobs from "{}".'.format(file))

        jobs = cls.new()
        if file.exists():
            with file.open('r', encoding='UTF-8') as fin:
                for line in fin:
                    jobs._jobs.append(Job.from_json(json.loads(line)))

        return jobs

    def add_job(self,
                query: Search.Query,
                max_tweets: int,
                batch_size: Optional[int] = None) -> None:
        self._jobs.append(Job(uuid4().hex, query, max_tweets, batch_size))

    def run(self, out_dir: Path, num_processes: int = 1) -> bool:
        logger = getLogger(__name__)
        logger.debug('Started running {:d} jobs.'.format(len(self._jobs)))

        Path.mkdir(out_dir, exist_ok=True, parents=True)

        with multiprocessing.Pool(processes=num_processes) as pool:
            result = min(pool.starmap(self._run_job,
                                      ((job, out_dir) for job in self._jobs)))

        if result:
            logger.info('All jobs completed successfully.')
        else:
            logger.error('Errors during job executing. Check log and run '
                         'again.')
        return result

    @classmethod
    def _run_job(cls, job: Job, out_dir: Path) -> bool:
        logger = getLogger(__name__)
        logger.info('Running job: {!r}'.format(job))

        meta_file = out_dir / job.meta_file_name
        data_file = out_dir / job.data_file_name

        if meta_file.exists():
            logger.debug('  Meta file already exists, loading information '
                         'from previous run.')

            with meta_file.open('r', encoding='UTF-8') as fin:
                previous_job = Job.from_json(json.load(fin))

            if not job.match(previous_job):
                logger.error('  Previous job description does not match '
                             'current one, manual intervention required! '
                             'If the already stored data is erroneous delete '
                             'the meta and data files of this job and rerun '
                             'this.')
                logger.error('    Meta file: {!s:s}'.format(meta_file))
                logger.error('    Data file: {!s:s}'.format(data_file))
                return False

            job = previous_job
            # Don't save previous exceptions back to file.
            job.exception = None

            if job.completed_at:
                logger.debug('  Skipping Job, because marked as completed at '
                             '"{}".'.format(
                    job.completed_at.strftime(NASTY_DATE_TIME_FORMAT)))
                return True

        if data_file.exists():
            logger.info('  Deleting previously created data file "{}" because '
                        'job execution did not complete.'.format(data_file))
            data_file.unlink()

        result = True
        try:
            tweets = list(Search(job.query, job.max_tweets, job.batch_size))
            with lzma.open(data_file, 'wt', encoding='UTF-8') as fout:
                for tweet in tweets:
                    fout.write('{:s}\n'.format(json.dumps(tweet.to_json())))

            job.completed_at = datetime.now()
        except Exception as e:
            logger.exception('  Job failed with exception.')
            job.exception = JsonSerializedException.from_exception(e)
            result = False

        with meta_file.open('w', encoding='UTF-8') as fout:
            json.dump(job.to_json(), fout, indent=2)

        return result
