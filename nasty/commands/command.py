from abc import ABC, abstractmethod
from argparse import ArgumentParser, Namespace as ArgumentNamespace
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
