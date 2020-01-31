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

from pathlib import Path

import pytest
from _pytest.capture import CaptureFixture
from _pytest.monkeypatch import MonkeyPatch

import nasty.cli._batch_command
from nasty.cli.main import main

from .mock_context import MockBatchContext


def test_correct_call(
    monkeypatch: MonkeyPatch, capsys: CaptureFixture, tmp_path: Path,
) -> None:
    mock_context = MockBatchContext()
    monkeypatch.setattr(
        nasty.cli._batch_command,
        nasty.cli._batch_command.Batch.__name__,  # type: ignore
        mock_context.MockBatch,
    )

    batch_file = tmp_path / "batch.jsonl"
    results_dir = tmp_path / "out"
    main(["batch", "--batch-file", str(batch_file), "--results-dir", str(results_dir)])

    assert mock_context.load_args == (batch_file,)
    assert mock_context.execute_args == (results_dir,)
    assert capsys.readouterr().out == ""


def test_no_batch_file(tmp_path: Path) -> None:
    batch_file = tmp_path / "batch.jsonl"
    results_dir = tmp_path / "out"

    with pytest.raises(FileNotFoundError):
        main(
            [
                "batch",
                "--batch-file",
                str(batch_file),
                "--results-dir",
                str(results_dir),
            ]
        )
