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

import sys
from logging import getLogger
from pathlib import Path
from typing import Any, Dict

import toml

from nasty._util.logging_ import setup_logging


def init_nasty() -> Dict[str, Any]:
    config = _load_config(get_source_folder() / "config.toml")

    setup_logging(config["log_level"])
    _log_config(config)

    return config


def get_source_folder() -> Path:
    return Path(__file__).parent.parent


def _load_config(path: Path) -> Dict[str, Any]:
    if not path.exists():
        print(
            'Could not find config file in "{}". Make sure you copy the '
            "example config file to this location and set your personal "
            "settings/secrets.".format(path),
            file=sys.stderr,
        )
        sys.exit()

    with path.open(encoding="UTF-8") as fin:
        config = toml.load(fin)

    return config


def _log_config(config: Dict[str, Any]):
    def hide_secrets(value, hidden=False):
        if isinstance(value, dict):
            return {
                k: hide_secrets(v, hidden=(hidden or ("secret" in k)))
                for k, v in value.items()
            }
        return "<hidden>" if hidden else value

    logger = getLogger(__name__)
    logger.debug("Loaded config:")
    for line in toml.dumps(hide_secrets(config)).splitlines():
        logger.debug("  " + line)
