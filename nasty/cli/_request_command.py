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

import json
from abc import ABC, abstractmethod
from argparse import ArgumentParser, _ArgumentGroup
from pathlib import Path
from typing import Generic, TypeVar

from overrides import overrides

from ..request.request import DEFAULT_BATCH_SIZE, Request
from ..request_executor import RequestExecutor
from ._command import _Command

_T_Request = TypeVar("_T_Request", bound=Request)


class _RequestCommand(_Command, ABC, Generic[_T_Request]):
    @classmethod
    @overrides
    def config_argparser(cls, argparser: ArgumentParser) -> None:
        cls._config_request_subclass_args(argparser)
        cls._config_request_args(argparser)
        cls._config_executor_args(argparser)

    @classmethod
    def _config_request_args(cls, argparser: ArgumentParser) -> _ArgumentGroup:
        g = argparser.add_argument_group(
            "Request Arguments", "Control how Tweets are requested."
        )
        g.add_argument(
            "-n",
            "--max-tweets",
            metavar="<N>",
            type=int,
            default=100,
            help=(
                "Maximum number of tweets to retrieve. Set to -1 to receive as many "
                "as possible. Defaults to 100."
            ),
        )
        g.add_argument(
            "-b",
            "--batch-size",
            metavar="<N>",
            type=int,
            default=-1,
            help=(
                "Batch size to retrieve Tweets in. Set to -1 for default behavior. "
                "Only change when necessary."
            ),
        )
        return g

    @classmethod
    def _config_request_subclass_args(cls, argparser: ArgumentParser) -> _ArgumentGroup:
        raise NotImplementedError()

    @classmethod
    def _config_executor_args(cls, argparser: ArgumentParser) -> _ArgumentGroup:
        g = argparser.add_argument_group(
            "Executor Arguments",
            "NASTY supports storing requests in a jobs file and executing them later "
            "via the 'nasty executor' command, which allows to operate in batch mode, "
            "track progress, and rerun uncompleted/failed requests.",
        )
        g.add_argument(
            "-e",
            "--to-executor",
            metavar="<FILE>",
            type=Path,
            help="Submit request to executor jobs file.",
        )
        return g

    def run(self) -> None:
        if self._args.max_tweets == -1:
            self._args.max_tweets = None
        if self._args.batch_size == -1:
            self._args.batch_size = DEFAULT_BATCH_SIZE

        request = self.build_request()
        if self._args.to_executor:
            request_executor = RequestExecutor()
            if self._args.to_executor.exists():
                request_executor.load_requests(self._args.to_executor)
            self._request_executor_submit(request_executor, request)
            request_executor.dump_requests(self._args.to_executor)
        else:
            for tweet in request.request():
                print(json.dumps(tweet.to_json()))  # noqa T001

    def _request_executor_submit(
        self, request_executor: RequestExecutor, request: _T_Request
    ) -> None:
        request_executor.submit(request)

    @abstractmethod
    def build_request(self) -> _T_Request:
        raise NotImplementedError()
