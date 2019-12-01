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

from nasty._util.misc import chunked

# -- test_chunked_* --------------------------------------------------------------------


def test_chunked_length_divisible() -> None:
    assert [[0, 1, 2], [3, 4, 5]] == list(chunked(3, range(6)))


def test_chunked_length_divisible_pad() -> None:
    assert [[0, 1, 2], [3, 4, 5]] == list(chunked(3, range(6), pad=True))


def test_chunked_length_not_divisible() -> None:
    assert [[0, 1, 2], [3, 4, 5], [6]] == list(chunked(3, range(7)))


def test_chunked_length_not_divisible_pad() -> None:
    assert [[0, 1, 2], [3, 4, 5], [6, None, None]] == list(
        chunked(3, range(7), pad=True)
    )


def test_chunked_length_not_divisible_pad_value() -> None:
    assert [[0, 1, 2], [3, 4, 5], [6, "x", "x"]] == list(
        chunked(3, range(7), pad=True, pad_value="x")
    )
