"""
Useful to check if user-agent needs to be changed.
But can also fail for empty searches (keyword-day).
"""
import unittest
from unittest import TestCase
import os
import gzip
import json
import tempfile
from datetime import date, timedelta
from typing import List, Tuple
from pathlib import Path
from nasty.old.jobs import run_jobs, build_jobs


def build_and_run_jobs_with_ape(tmp_out):
    keyword = ["ape"]
    start = date(2019, 8, 13)
    lang = "en"
    job = build_jobs(keyword, start, start + timedelta(days=1), lang)
    run_jobs(job, 1, tmp_out)


class TestForEmptyFilesMarkedCompleted(TestCase):
    def test_out_dictionary_files(self):
        with tempfile.TemporaryDirectory() as tmp_out:
            tmp_out = Path(tmp_out)
            build_and_run_jobs_with_ape(tmp_out)

            meta_files, data_files = load_file_paths(tmp_out)
            is_failed = False
            failed_files = []
            for meta_file, data_file in zip(meta_files, data_files):
                meta_file = tmp_out / meta_file
                data_file = tmp_out / data_file
                with meta_file.open("rt", encoding="UtF-8") as meta:
                    meta = json.load(meta)
                    if meta["completed-at"] is not None:
                        if gz_is_empty(data_file):
                            # if os.stat(data_file).st_size == 0:
                            is_failed = True
                            failed_files.append(meta_file)
            if is_failed:
                print(f"{len(failed_files)} empty files, "
                      f"that were marked as completed. Files:")
                for filename in failed_files:
                    print(filename.name)
                self.fail("The data file was empty.")


def load_file_paths(folder) -> \
        Tuple[List[Path], List[Path]]:
    # folder: path for parameter resulted in the inspection showing
    # listdir(folder) as "wanted 'T' got 'Path', but would still run fine
    meta_files = []
    data_files = []
    # First looking for the data file, to circumvent that the data file doesn't
    # exist yet. (e.g. ConnectionError during download)
    for file in [f for f in os.listdir(folder) if f.endswith("data.jsonl.gz")]:
        data_files.append(Path(file))
        file = file.replace("data.jsonl.gz", "meta.json")
        meta_files.append(Path(file))
    data_files.sort()
    meta_files.sort()
    return meta_files, data_files


# Code found at: https://stackoverflow.com/a/37875919 2019-09-02
def gz_is_empty(fname):
    """ Test if gzip file fname is empty
        Return True if the uncompressed data in fname has zero length
        or if fname itself has zero length
        Raises OSError if fname has non-zero length and is not a gzip file
    """
    with gzip.open(fname, 'rb') as f:
        data = f.read(1)
    return len(data) == 0


if __name__ == '__main__':
    unittest.main()
