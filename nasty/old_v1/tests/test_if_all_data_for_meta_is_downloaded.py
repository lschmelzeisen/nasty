"""
Test if your crawl is complete.

Checks if all meta files are marked as completed. (Done each rerun of nasty)
Checks if all meta files have a data file. (Not tested in test_for_empty_fil..)
Checks if data files are filled. (Checked in test_for_empty_files_marked_com..)
"""

import unittest
from pathlib import Path
from unittest import TestCase
from typing import List
import os
import json
from nasty.tests.old.test_for_empty_files_marked_completed import gz_is_empty


def make_paths_from_filenames(folder: Path, files: List[str]) -> \
        List[Path]:
    paths = []
    for file in files:
        paths.append(folder / file)
    paths.sort()
    return paths


class TestIfAllDataForMetaIsDownloaded(TestCase):

    def test_if_all_marked_completed(self):
        out_directory = Path().absolute().parent.parent / "out"
        meta_filenames = [f for f in os.listdir(out_directory)
                          if f.endswith("meta.json")]
        meta_files = make_paths_from_filenames(out_directory, meta_filenames)
        is_failed = False
        failed_files = []
        for meta_file in meta_files:
            with meta_file.open("rt", encoding="UTF-8") as meta:
                meta = json.load(meta)
                if meta["completed-at"] is None:
                    is_failed = True
                    failed_files.append(meta_file)

        if is_failed:
            print(f"{len(failed_files)} meta files are not marked complete.")
            for file in failed_files:
                print(file)
            self.fail("Not all meta files are marked as completed.")

    def test_if_all_meta_have_data_files(self):
        out_directory = Path().absolute().parent.parent / "out"
        meta_filenames = [f for f in os.listdir(out_directory)
                          if f.endswith("meta.json")]
        is_failed = False
        failed_files = []
        for meta_filename in meta_filenames:
            meta_filename = meta_filename.replace("meta.json", "data.jsonl.gz")
            data_file = out_directory / meta_filename
            if not data_file.exists():
                is_failed = True
                failed_files.append(data_file)
        if is_failed:
            print(f"{len(failed_files)} meta files have no data files.")
            for file in failed_files:
                print(file)
            self.fail("Not all meta files have corresponding data files.")

    def test_for_empty_data_files(self):
        out_directory = Path().absolute().parent.parent / "out"
        meta_filenames = [f for f in os.listdir(out_directory)
                          if f.endswith("meta.json")]
        is_failed = False
        failed_files = []
        for meta_filename in meta_filenames:
            meta_filename = meta_filename.replace("meta.json", "data.jsonl.gz")
            data_file = out_directory / meta_filename
            if gz_is_empty(data_file):
                is_failed = True
                failed_files.append(data_file)
        if is_failed:
            print(f"{len(failed_files)} meta files have empty data files.")
            for file in failed_files:
                print(file)
            self.fail("Not all data files are filled.")


if __name__ == '__main__':
    unittest.main()
