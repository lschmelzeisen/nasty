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

import lzma
from contextlib import contextmanager
from pathlib import Path
from typing import Iterable, Iterator, TextIO, cast


@contextmanager
def _read_file(file: Path, *, use_lzma: bool = False) -> Iterator[TextIO]:
    if use_lzma:
        with lzma.open(file, "rt", encoding="UTF-8") as fin:
            yield cast(TextIO, fin)
    else:
        with file.open("r", encoding="UTF-8") as fin:
            yield fin


@contextmanager
def _write_file_with_tmp_guard(
    file: Path, *, overwrite_existing: bool = False, use_lzma: bool = False
) -> Iterator[TextIO]:
    if not overwrite_existing and file.exists():
        raise ValueError(
            "File '{}' to be written to, already exists. Manual intervention required! "
            "Check file and delete if no longer needed.".format(file)
        )

    tmp_file = file.parent / (".tmp." + file.name)

    if use_lzma:
        with lzma.open(tmp_file, "wt", encoding="UTF-8") as fin:
            yield cast(TextIO, fin)
    else:
        with tmp_file.open("w", encoding="UTF-8") as fin:
            yield fin

    tmp_file.rename(file)


def read_file(file: Path, *, use_lzma: bool = False) -> str:
    with _read_file(file, use_lzma=use_lzma) as fin:
        return fin.read()


def write_file(
    file: Path, value: str, *, overwrite_existing: bool = False, use_lzma: bool = False
) -> None:
    with _write_file_with_tmp_guard(
        file, overwrite_existing=overwrite_existing, use_lzma=use_lzma
    ) as fout:
        fout.write(value)


def read_lines_file(file: Path, *, use_lzma: bool = False) -> Iterable[str]:
    with _read_file(file, use_lzma=use_lzma) as fin:
        for line in fin:
            yield line.strip()


def write_lines_file(
    file: Path,
    values: Iterable[str],
    *,
    overwrite_existing: bool = False,
    use_lzma: bool = False,
) -> None:
    with _write_file_with_tmp_guard(
        file, overwrite_existing=overwrite_existing, use_lzma=use_lzma
    ) as fout:
        for value in values:
            fout.write(value)
            fout.write("\n")
