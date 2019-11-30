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

from typing import Any, Callable, Iterable, Optional, TypeVar, Union

_T_arg = TypeVar("_T_arg")
_T_func = TypeVar("_T_func", bound=Callable[..., Any])

class mark:  # noqa: N801
    @staticmethod
    def parametrize(
        argnames: str,
        argvalues: Iterable[_T_arg],
        indirect: bool = ...,
        ids: Optional[Union[Iterable[str], Callable[[_T_arg], str]]] = ...,
        scope: Optional[str] = ...,
    ) -> Callable[[_T_func], _T_func]: ...
