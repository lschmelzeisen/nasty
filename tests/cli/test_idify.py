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

import json
from contextlib import contextmanager
from copy import deepcopy
from io import StringIO
from pathlib import Path
from types import ModuleType
from typing import Iterator

from _pytest.capture import CaptureFixture
from _pytest.monkeypatch import MonkeyPatch

import nasty.cli._idify_command
import nasty.cli._unidify_command
from nasty.cli.main import main
from nasty.tweet.tweet import Tweet

from ..test_tweet import tweet_jsons
from .mock_context import MockBatchResultsContext


@contextmanager
def _mock_stdin(module: ModuleType, content: str) -> Iterator[None]:
    """Can't do regular mock here, because that it will fail with pytest's capsys."""

    # Need to use getattr/setattr and hide warnings for those via noqa here, because I
    # do not know how to type the module argument so that mypy understands module.stdin.
    old_stdin = getattr(module, "stdin")  # noqa: B009
    setattr(module, "stdin", StringIO(content))  # noqa: B010
    yield None
    setattr(module, "stdin", old_stdin)  # noqa: B010


def test_idify_stdin(capsys: CaptureFixture) -> None:
    tweet_json = tweet_jsons["1142944425502543875"]
    tweets = []
    for i in range(5):
        tweet = deepcopy(tweet_json)
        tweet["id"] = i
        tweet["id_str"] = str(i)
        tweets.append(tweet)

    with _mock_stdin(
        nasty.cli._idify_command, "\n".join(json.dumps(tweet) for tweet in tweets),
    ):
        main(["idify"])
    assert capsys.readouterr().out == "\n".join(str(i) for i in range(5)) + "\n"


def test_idify_indir(monkeypatch: MonkeyPatch, tmp_path: Path) -> None:
    mock_context = MockBatchResultsContext()
    monkeypatch.setattr(
        nasty.cli._idify_command,
        nasty.cli._idify_command.BatchResults.__name__,  # type: ignore
        mock_context.MockBatchResults,
    )

    main(["idify", "--in-dir", str(tmp_path)])

    assert mock_context.init_args == (tmp_path,)
    assert mock_context.idify_args == (tmp_path,)
    assert mock_context.unidify_args is None


def test_idify_indir_outdir(monkeypatch: MonkeyPatch, tmp_path: Path) -> None:
    in_dir = tmp_path / "in"
    out_dir = tmp_path / "out"

    mock_context = MockBatchResultsContext()
    monkeypatch.setattr(
        nasty.cli._idify_command,
        nasty.cli._idify_command.BatchResults.__name__,  # type: ignore
        mock_context.MockBatchResults,
    )

    main(["idify", "--in-dir", str(in_dir), "--out-dir", str(out_dir)])

    assert mock_context.init_args == (in_dir,)
    assert mock_context.idify_args == (out_dir,)
    assert mock_context.unidify_args is None


def test_unidify_std(capsys: CaptureFixture) -> None:
    with _mock_stdin(
        nasty.cli._unidify_command,
        "\n".join(
            ("1115690002233556993", "1115690615612825601", "1115691710657499137")
        ),
    ):
        main(["unidify"])

    assert [
        "We encourage submissions of new, previously, or concurrently published "
        "research. The event should be a forum for researchers to exchange ideas, "
        "discuss work, and get feedback. We hope you'll consider submitting your work.",
        "We'll have talks from research leaders on the latest advances in NLP. "
        "@NandoDF will be giving the keynote and more speakers will be announced soon. "
        "https://t.co/SB3URxn6ab",
        "Registration will open soon. In the meantime, we'll hope you'll save the date "
        "and consider joining us for what should be a fun day of listening to "
        "stimulating talks, mingling with like-minded people, exchanging ideas, and "
        "maybe even striking up a collaboration.",
    ] == [
        Tweet(json.loads(line)).text
        for line in capsys.readouterr().out.strip().split("\n")
    ]


def test_unidify_indir(monkeypatch: MonkeyPatch, tmp_path: Path) -> None:
    mock_context = MockBatchResultsContext()
    monkeypatch.setattr(
        nasty.cli._unidify_command,
        nasty.cli._unidify_command.BatchResults.__name__,  # type: ignore
        mock_context.MockBatchResults,
    )

    main(["unidify", "--in-dir", str(tmp_path)])

    assert mock_context.init_args == (tmp_path,)
    assert mock_context.idify_args is None
    assert mock_context.unidify_args == (tmp_path,)


def test_unidify_indir_outdir(monkeypatch: MonkeyPatch, tmp_path: Path) -> None:
    in_dir = tmp_path / "in"
    out_dir = tmp_path / "out"

    mock_context = MockBatchResultsContext()
    monkeypatch.setattr(
        nasty.cli._unidify_command,
        nasty.cli._unidify_command.BatchResults.__name__,  # type: ignore
        mock_context.MockBatchResults,
    )

    main(["unidify", "--in-dir", str(in_dir), "--out-dir", str(out_dir)])

    assert mock_context.init_args == (in_dir,)
    assert mock_context.idify_args is None
    assert mock_context.unidify_args == (out_dir,)
