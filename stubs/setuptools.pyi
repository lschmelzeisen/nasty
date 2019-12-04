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

from typing import Mapping, Sequence

def find_packages(
    where: str = ..., exclude: Sequence[str] = ..., include: Sequence[str] = ...
) -> Sequence[str]: ...
def setup(
    name: str,
    use_scm_version: Mapping[str, str],
    description: str,
    long_description: str,
    long_description_content_type: str,
    author: str,
    author_email: str,
    license: str,  # noqa: A002
    classifiers: Sequence[str],
    keywords: Sequence[str],
    packages: Sequence[str],
    python_requires: str,
    setup_requires: Sequence[str],
    install_requires: Sequence[str],
    extras_require: Mapping[str, Sequence[str]],
    entry_points: Mapping[str, Sequence[str]],
    project_urls: Mapping[str, str],
) -> None: ...
