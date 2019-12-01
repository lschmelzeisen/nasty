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

from abc import ABC, abstractmethod
from argparse import ArgumentParser
from argparse import Namespace as ArgumentNamespace
from typing import List


class Command(ABC):
    @classmethod
    @abstractmethod
    def command(cls) -> str:
        raise NotImplementedError()

    @classmethod
    @abstractmethod
    def aliases(cls) -> List[str]:
        raise NotImplementedError()

    @classmethod
    @abstractmethod
    def description(cls) -> str:
        raise NotImplementedError()

    @classmethod
    @abstractmethod
    def config_argparser(cls, argparser: ArgumentParser) -> None:
        raise NotImplementedError()

    def __init__(self, args: ArgumentNamespace):
        self._args = args

    @abstractmethod
    def run(self) -> None:
        raise NotImplementedError()