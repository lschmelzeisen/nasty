import json
import lzma
import multiprocessing
from abc import ABC, abstractmethod
from datetime import datetime
from logging import getLogger
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4

from nasty.retrieval.replies import Replies
from nasty.retrieval.search import Search
from nasty.retrieval.thread import Thread
from nasty.retrieval.timeline import Timeline
from nasty.util.consts import NASTY_DATE_TIME_FORMAT
from nasty.util.json import JsonSerializedException


class _Work(ABC):
    def __init__(self,
                 type_: str,
                 max_tweets: Optional[int] = 100,
                 batch_size: Optional[int] = None):
        self.type = type_
        self.max_tweets = max_tweets
        self.batch_size = batch_size

    def __repr__(self) -> str:
        return type(self).__name__ + repr(self.to_json())

    def __eq__(self, other: '_Work') -> bool:
        return (type(self) == type(other)) and (self.__dict__ == other.__dict__)

    @abstractmethod
    def to_timeline(self) -> Timeline:
        raise NotImplementedError()

    @abstractmethod
    def to_json(self) -> Dict[str, Any]:
        raise NotImplementedError()

    @classmethod
    @abstractmethod
    def from_json(cls, obj: Dict[str, Any]) -> '_Work':
        if obj['type'] == 'search':
            return _SearchWork.from_json(obj)
        elif obj['type'] == 'replies':
            return _RepliesWork.from_json(obj)
        elif obj['type'] == 'thread':
            return _ThreadWork.from_json(obj)
        else:
            raise RuntimeError('Unknown work type: "{}".'.format(obj['type']))


class _SearchWork(_Work):
    def __init__(self,
                 query: Search.Query,
                 max_tweets: Optional[int],
                 batch_size: Optional[int]):
        super().__init__('search', max_tweets, batch_size)
        self.query = query

    def to_timeline(self) -> Search:
        return Search(self.query, self.max_tweets, self.batch_size)

    def to_json(self) -> Dict[str, Any]:
        obj = {
            'type': self.type,
            'query': self.query.to_json(),
        }

        if self.max_tweets is not None:
            obj['max_tweets'] = self.max_tweets
        if self.batch_size is not None:
            obj['batch_size'] = self.batch_size

        return obj

    @classmethod
    def from_json(cls, obj: Dict[str, Any]) -> '_SearchWork':
        assert obj['type'] == 'search'
        return cls(Search.Query.from_json(obj['query']),
                   obj.get('max_tweets'),
                   obj.get('batch_size'))


class _RepliesWork(_Work):
    def __init__(self,
                 tweet_id: str,
                 max_tweets: Optional[int],
                 batch_size: Optional[int]):
        super().__init__('replies', max_tweets, batch_size)
        self.tweet_id = tweet_id

    def to_timeline(self) -> Replies:
        return Replies(self.tweet_id, self.max_tweets, self.batch_size)

    def to_json(self) -> Dict[str, Any]:
        obj = {
            'type': self.type,
            'tweet_id': self.tweet_id,
        }

        if self.max_tweets is not None:
            obj['max_tweets'] = self.max_tweets
        if self.batch_size is not None:
            obj['batch_size'] = self.batch_size

        return obj

    @classmethod
    def from_json(cls, obj: Dict[str, Any]) -> '_RepliesWork':
        assert obj['type'] == 'replies'
        return cls(
            obj['tweet_id'], obj.get('max_tweets'), obj.get('batch_size'))


class _ThreadWork(_Work):
    def __init__(self,
                 tweet_id: str,
                 max_tweets: Optional[int],
                 batch_size: Optional[int]):
        super().__init__('thread', max_tweets, batch_size)
        self.tweet_id = tweet_id

    def to_timeline(self) -> Thread:
        return Thread(self.tweet_id, self.max_tweets, self.batch_size)

    def to_json(self) -> Dict[str, Any]:
        obj = {
            'type': self.type,
            'tweet_id': self.tweet_id,
        }

        if self.max_tweets is not None:
            obj['max_tweets'] = self.max_tweets
        if self.batch_size is not None:
            obj['batch_size'] = self.batch_size

        return obj

    @classmethod
    def from_json(cls, obj: Dict[str, Any]) -> '_ThreadWork':
        assert obj['type'] == 'thread'
        return cls(
            obj['tweet_id'], obj.get('max_tweets'), obj.get('batch_size'))


class _Job:
    def __init__(self,
                 id_: str,
                 work: _Work,
                 completed_at: Optional[datetime] = None,
                 exception: Optional[JsonSerializedException] = None):
        self.id = id_
        self.work = work
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

    def to_json(self) -> Dict[str, Any]:
        obj = {
            'id': self.id,
            'work': self.work.to_json(),
        }

        if self.completed_at:
            obj['completed_at'] = \
                self.completed_at.strftime(NASTY_DATE_TIME_FORMAT)

        if self.exception is not None:
            obj['exception'] = self.exception.to_json()

        return obj

    @classmethod
    def from_json(cls, obj: Dict[str, Any]) -> '_Job':
        return cls(id_=obj['id'],
                   work=_Work.from_json(obj['work']),
                   completed_at=(datetime.strptime(obj['completed_at'],
                                                   NASTY_DATE_TIME_FORMAT)
                                 if 'completed_at' in obj else None),
                   exception=(
                       JsonSerializedException.from_json(obj['exception'])
                       if 'exception' in obj else None))


class Jobs:
    def __init__(self, jobs: List[_Job]):
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
        with file.open('r', encoding='UTF-8') as fin:
            for line in fin:
                jobs._jobs.append(_Job.from_json(json.loads(line)))

        return jobs

    def add_search_job(self,
                       query: Search.Query,
                       max_tweets: Optional[int] = 100,
                       batch_size: Optional[int] = None) -> None:
        self._jobs.append(
            _Job(uuid4().hex, _SearchWork(query, max_tweets, batch_size)))

    def add_replies_job(self,
                        tweet_id: str,
                        max_tweets: Optional[int] = 100,
                        batch_size: Optional[int] = None) -> None:
        self._jobs.append(
            _Job(uuid4().hex, _RepliesWork(tweet_id, max_tweets, batch_size)))

    def add_thread_job(self,
                       tweet_id: str,
                       max_tweets: Optional[int] = 100,
                       batch_size: Optional[int] = None) -> None:
        self._jobs.append(
            _Job(uuid4().hex, _ThreadWork(tweet_id, max_tweets, batch_size)))

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
    def _run_job(cls, job: _Job, out_dir: Path) -> bool:
        logger = getLogger(__name__)
        logger.info('Running job: {!r}'.format(job))

        meta_file = out_dir / job.meta_file_name
        data_file = out_dir / job.data_file_name

        if meta_file.exists():
            logger.debug('  Meta file already exists, loading information '
                         'from previous run.')

            with meta_file.open('r', encoding='UTF-8') as fin:
                previous_job = _Job.from_json(json.load(fin))

            if job.work != previous_job.work:
                logger.error('  Previous job work does not match current one, '
                             'manual intervention required! If the already '
                             'stored data is erroneous delete the meta and '
                             'data files of this job and rerun this.')
                logger.error('    Meta file: {!s:s}'.format(meta_file))
                logger.error('    Data file: {!s:s}'.format(data_file))
                return False

            if previous_job.completed_at:
                logger.debug(
                    '  Skipping Job, because marked as completed at '
                    '"{}".'.format(previous_job.completed_at
                                   .strftime(NASTY_DATE_TIME_FORMAT)))
                return True

            job = previous_job
            # Don't save previous exceptions back to file.
            job.exception = None

        if data_file.exists():
            logger.info('  Deleting previously created data file "{}" because '
                        'job execution did not complete.'.format(data_file))
            data_file.unlink()

        result = True
        try:
            tweets = list(job.work.to_timeline())
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
