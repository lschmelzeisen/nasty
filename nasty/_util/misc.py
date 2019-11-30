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

from itertools import zip_longest
from typing import Iterable, Optional, Sequence, TypeVar

_T_item = TypeVar("_T_item")


def chunked(
    chunk_size: int,
    iterable: Iterable[_T_item],
    pad: bool = False,
    pad_value: Optional[_T_item] = None,
) -> Iterable[Sequence[_T_item]]:
    """Separate an iterable into equal size chunks."""

    iters = [iter(iterable)] * chunk_size
    for chunk in zip_longest(*iters, fillvalue=pad_value):
        if pad:
            yield list(chunk)
        else:
            yield [item for item in chunk if item is not None]
