import json
import logging
import lzma
import unittest
from datetime import date, datetime
from http import HTTPStatus
from logging import getLogger
from pathlib import Path

import responses

from nasty.jobs import Job, Jobs
from nasty.retrieval.search import Search
from nasty.tests.requests_cache import RequestsCache
from nasty.tweet import Tweet
from nasty.util.disrespect_robotstxt import disrespect_robotstxt
from nasty.util.json import JsonSerializedException
from nasty.util.logging import setup_logging
from nasty.util.path import TemporaryDirectoryPath, TemporaryFilePath

setup_logging(logging.DEBUG)


class TestJobDumpLoad(unittest.TestCase):
    def test_search_job_trump(self):
        job = Job(_SearchWork(Search.Query('trump'), 1000, None))
        self.assertEqual(job, Job.from_json(job.to_json()))

    def test_search_job_trump_completed_at(self):
        job = Job(_SearchWork(Search.Query('trump'), 10000, 100),
                  completed_at=datetime.now())
        self.assertEqual(job, Job.from_json(job.to_json()))

    def test_search_job_trump_exceptions(self):
        # Collect exception with trace.
        try:
            raise ValueError('Test Error.')
        except ValueError as e:
            exception = JsonSerializedException.from_exception(e)

        job = Job(_SearchWork(Search.Query('trump'), 10, 1),
                  exception=exception)
        self.assertEqual(job, Job.from_json(job.to_json()))

    def test_replies_job(self):
        job = Job(_RepliesWork('332308211321425920', None, None))
        self.assertEqual(job, Job.from_json(job.to_json()))

    def test_thread_job(self):
        job = Job(_ThreadWork('332308211321425920', 123, 456))
        self.assertEqual(job, Job.from_json(job.to_json()))


class TestJobsDumpLoad(unittest.TestCase):
    def test_single_search_job(self):
        def run_test(*work_args, **work_kwargs) -> None:
            jobs = Jobs.new()
            jobs.add(Job.new(_SearchWork(*work_args, **work_kwargs)))
            with TemporaryFilePath(prefix='nasty-test-',
                                   suffix='.jsonl') as temp_file:
                jobs.dump(temp_file)

                with temp_file.open('r', encoding='UTF-8') as fin:
                    lines = fin.readlines()
                self.assertEqual(1, len(lines))
                self.assertNotEqual(0, len(lines[0]))

                self.assertEqual(jobs, Jobs.load(temp_file))

        run_test(Search.Query('trump'), max_tweets=50)
        run_test(Search.Query('hillary',
                              filter=Search.Query.Filter.PHOTOS, lang='de'),
                 max_tweets=500, batch_size=1)
        run_test(Search.Query('obama',
                              since=date(2009, 1, 20), until=date(2017, 1, 20)),
                 max_tweets=5, batch_size=1000)

    def test_many_search_jobs(self):
        def run_test(num_jobs) -> None:
            jobs = Jobs.new()
            for i in range(1, num_jobs + 1):
                jobs.add_search_job(
                    Search.Query(str(i)), max_tweets=i, batch_size=i)
            with TemporaryFilePath(prefix='nasty-test-',
                                   suffix='.jsonl') as temp_file:
                jobs.dump(temp_file)

                with temp_file.open('r', encoding='UTF-8') as fin:
                    lines = fin.readlines()
                self.assertEqual(num_jobs, len(lines))
                for line in lines:
                    self.assertNotEqual(0, len(line))

                self.assertEqual(jobs, Jobs.load(temp_file))

        run_test(10)
        run_test(5005)
        run_test(10000)


class TestSearchJobsRun(unittest.TestCase):
    @RequestsCache()
    @disrespect_robotstxt
    def test_success(self):
        jobs = Jobs.new()
        jobs.add_search_job(Search.Query('trump'), max_tweets=50)
        jobs.add_search_job(Search.Query('hillary'), max_tweets=50)
        jobs.add_search_job(Search.Query('obama'), max_tweets=50)

        with TemporaryDirectoryPath(prefix='nasty-test-') as temp_dir:
            self.assertTrue(jobs.run(temp_dir))
            self._assert_out_dir_structure(temp_dir, jobs)

    @RequestsCache()
    @disrespect_robotstxt
    def test_success_parallel(self):
        jobs = Jobs.new()
        for i in range(16):
            jobs.add_search_job(Search.Query('trump',
                                             since=date(2019, 1, i + 1),
                                             until=date(2019, 1, i + 2)),
                                max_tweets=50)

        with TemporaryDirectoryPath(prefix='nasty-test-') as temp_dir:
            self.assertTrue(jobs.run(temp_dir, num_processes=4))
            self._assert_out_dir_structure(temp_dir, jobs)

    @RequestsCache()
    @disrespect_robotstxt
    def test_success_empty(self):
        # Random string that currently does not match any Tweet.
        unknown_word = 'c9dde8b5451149e683d4f07e4c4348ef'
        jobs = Jobs.new()
        jobs.add_search_job(Search.Query(unknown_word), max_tweets=50)

        with TemporaryDirectoryPath(prefix='nasty-test-') as temp_dir:
            self.assertTrue(jobs.run(temp_dir))
            self._assert_out_dir_structure(temp_dir, jobs)
            with lzma.open(temp_dir / jobs._jobs[0].data_file_name,
                           'rb') as fin:
                data = fin.read()
            self.assertEqual(0, len(data))

    @RequestsCache()
    @disrespect_robotstxt
    def test_previous_match(self):
        jobs = Jobs.new()
        jobs.add_search_job(Search.Query('trump'), max_tweets=50)

        with TemporaryDirectoryPath(prefix='nasty-test-') as temp_dir:
            # Create stray (but matching) meta file.
            job = jobs._jobs[0]
            meta_file = temp_dir / job.meta_file_name
            with meta_file.open('w', encoding='UTF-8') as fout:
                json.dump(job.to_json(), fout, indent=2)
            meta_stat1 = meta_file.stat()

            # Run and verify that this works without problems.
            self.assertTrue(jobs.run(temp_dir))
            self._assert_out_dir_structure(temp_dir, jobs)
            meta_stat2 = meta_file.stat()
            self.assertLess(meta_stat1.st_mtime_ns, meta_stat2.st_mtime_ns)

    @RequestsCache()
    @disrespect_robotstxt
    def test_previous_no_match(self):
        jobs = Jobs.new()
        jobs.add_search_job(Search.Query('trump'), max_tweets=50)

        with TemporaryDirectoryPath(prefix='nasty-test-') as temp_dir:
            # Run successful crawl with 'trump' and verify.
            self.assertTrue(jobs.run(temp_dir))
            self._assert_out_dir_structure(temp_dir, jobs)

            # Change job to instead query for 'obama'.
            meta_file = temp_dir / jobs._jobs[0].meta_file_name
            with meta_file.open('r', encoding='UTF-8') as fin:
                job = Job.from_json(json.load(fin))
            job.work.query.query = 'obama'
            jobs._jobs[0] = job

            # Verify that this fails because of job description mismatch.
            self.assertFalse(jobs.run(temp_dir))

            # Delete offending job meta file, run again, and verify.
            meta_file.unlink()
            self.assertTrue(jobs.run(temp_dir))
            self._assert_out_dir_structure(temp_dir, jobs)

    @RequestsCache()
    @disrespect_robotstxt
    def test_previous_completed(self):
        jobs = Jobs.new()
        jobs.add_search_job(Search.Query('trump'), max_tweets=50)

        with TemporaryDirectoryPath(prefix='nasty-test-') as temp_dir:
            meta_file = temp_dir / jobs._jobs[0].meta_file_name
            data_file = temp_dir / jobs._jobs[0].data_file_name

            # Run job and verify.
            self.assertTrue(jobs.run(temp_dir))
            self._assert_out_dir_structure(temp_dir, jobs)
            meta_stat1 = meta_file.stat()
            data_stat1 = data_file.stat()

            # Run job again (should skip the completed job), and verify.
            self.assertTrue(jobs.run(temp_dir))
            self._assert_out_dir_structure(temp_dir, jobs)
            meta_stat2 = meta_file.stat()
            data_stat2 = data_file.stat()

            # Verify that files were not modified.
            self.assertLessEqual(meta_stat1.st_atime_ns, meta_stat2.st_atime_ns)
            self.assertEqual(meta_stat1.st_mtime_ns, meta_stat2.st_mtime_ns)
            self.assertEqual(data_stat1.st_atime_ns, data_stat2.st_atime_ns)
            self.assertEqual(data_stat1.st_mtime_ns, data_stat2.st_mtime_ns)

    @RequestsCache()
    @disrespect_robotstxt
    def test_previous_stray_data(self):
        jobs = Jobs.new()
        jobs.add_search_job(Search.Query('trump'), max_tweets=50)

        with TemporaryDirectoryPath(prefix='nasty-test-') as temp_dir:
            # Create stray data file (with invalid data, but is irrelevant).
            job = jobs._jobs[0]
            data_file = temp_dir / job.data_file_name
            with data_file.open('w', encoding='UTF-8') as fout:
                fout.write('INVALID DATA')
            data_stat1 = data_file.stat()

            # Run and verify that this works without problems.
            self.assertTrue(jobs.run(temp_dir))
            self._assert_out_dir_structure(temp_dir, jobs)
            data_stat2 = data_file.stat()
            self.assertLess(data_stat1.st_mtime_ns, data_stat2.st_mtime_ns)

    @responses.activate
    @disrespect_robotstxt
    def test_exception_internal_server_error(self):
        # Simulate 500 Internal Server Error on first request to Twitter.
        responses.add(responses.GET, 'https://mobile.twitter.com/robots.txt',
                      body='Crawl-delay: 1')
        responses.add(responses.GET, 'https://mobile.twitter.com/search',
                      match_querystring=False,
                      status=HTTPStatus.INTERNAL_SERVER_ERROR.value)

        jobs = Jobs.new()
        jobs.add_search_job(Search.Query('trump'), max_tweets=50)

        with TemporaryDirectoryPath(prefix='nasty-test-') as temp_dir:
            # Run and verify that appropriate exception was logged.
            self.assertFalse(jobs.run(temp_dir))
            with (temp_dir / jobs._jobs[0].meta_file_name).open(
                    'r', encoding='UTF-8') as fin:
                job = Job.from_json(json.load(fin))
            self.assertEqual(job.exception.type,
                             'UnexpectedStatusCodeException')

    def _assert_out_dir_structure(self,
                                  out_dir: Path,
                                  jobs: Jobs,
                                  allow_empty: bool = False) -> None:
        logger = getLogger(__name__)

        self.assertTrue(out_dir.exists())

        files = list(out_dir.iterdir())
        self.assertNotEqual(0, len(files))

        for job in jobs._jobs:
            meta_file = out_dir / job.meta_file_name
            self.assertTrue(meta_file.exists())
            files.remove(meta_file)

            with meta_file.open('r', encoding='UTF-8') as fin:
                completed_job = Job.from_json(json.load(fin))

            self.assertTrue(job.work == completed_job.work)
            self.assertGreater(datetime.now(), completed_job.completed_at)
            self.assertIsNone(completed_job.exception)

            data_file = out_dir / job.data_file_name
            self.assertTrue(data_file.exists())
            files.remove(data_file)

            with lzma.open(data_file, 'rt', encoding='UTF-8') as fin:
                tweets = []
                for line in fin:
                    self.assertIn(job.work.query.query, line.lower())
                    tweets.append(Tweet.from_json(json.loads(line)))

            if not allow_empty:
                continue

            self.assertLess(0, len(tweets))
            self.assertGreaterEqual(job.max_tweets, len(tweets))
            if len(tweets) != job.max_tweets:
                logger.warning('Found only {:d} tweets which is less than '
                               'requests max_tweets = {:d}.'.format(
                    len(tweets), job.max_tweets))

        for file in files:
            logger.error('Extra file in output directory: {:s}'.format(file))
        self.assertEqual(0, len(files))


if __name__ == '__main__':
    unittest.main()
