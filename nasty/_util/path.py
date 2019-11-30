#
# Copyright 2019 Lukas Schmelzeisen
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

from contextlib import contextmanager
from pathlib import Path
from tempfile import NamedTemporaryFile, TemporaryDirectory

from overrides import overrides


@contextmanager
def TemporaryFilePath(*args, **kwargs):  # noqa: N802
    file = NamedTemporaryFile(*args, **kwargs, delete=False)
    path = Path(file.name)
    file.close()

    try:
        yield path
    finally:
        path.unlink()


class TemporaryDirectoryPath(TemporaryDirectory):
    @overrides
    def __enter__(self) -> Path:
        return Path(super().__enter__())
