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

import argparse
from abc import ABC, abstractmethod
from argparse import ArgumentParser
from typing import Sequence


class _Command(ABC):
    @classmethod
    @abstractmethod
    def command(cls) -> str:
        raise NotImplementedError()

    @classmethod
    @abstractmethod
    def aliases(cls) -> Sequence[str]:
        raise NotImplementedError()

    @classmethod
    @abstractmethod
    def description(cls) -> str:
        raise NotImplementedError()

    @classmethod
    @abstractmethod
    def config_argparser(cls, argparser: ArgumentParser) -> None:
        pass

    def __init__(self, args: argparse.Namespace):
        self._args = args

    def validate_arguments(self, argparser: ArgumentParser) -> None:
        pass

    @abstractmethod
    def run(self) -> None:
        raise NotImplementedError()
