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

from logging import getLogger
from pathlib import Path
from typing import Optional

from nasty_utils import (
    ColoredBraceStyleAdapter,
    LoggingSettings,
    Settings,
    SettingsConfig,
)
from pydantic import SecretStr, validator

_LOGGER = ColoredBraceStyleAdapter(getLogger(__name__))

_T_VALIDATOR = classmethod


def _key_validator(v: object) -> Optional[str]:
    if not isinstance(v, str) or v.startswith("Enter Twitter "):
        return None
    return v


class TwitterApiSettings(Settings):
    consumer_api_key: Optional[SecretStr]
    _consumer_api_key_validator: _T_VALIDATOR = validator(
        "consumer_api_key", pre=True, allow_reuse=True
    )(_key_validator)

    consumer_api_secret: Optional[SecretStr]
    _consumer_api_secret_validator: _T_VALIDATOR = validator(
        "consumer_api_secret", pre=True, allow_reuse=True
    )(_key_validator)

    access_token: Optional[SecretStr]
    _access_token_validator: _T_VALIDATOR = validator(
        "access_token", pre=True, allow_reuse=True
    )(_key_validator)

    access_token_secret: Optional[SecretStr]
    _access_token_secret_validator: _T_VALIDATOR = validator(
        "access_token_secret", pre=True, allow_reuse=True
    )(_key_validator)


class NastySettings(LoggingSettings):
    class Config(SettingsConfig):
        search_path = Path("nasty.toml")

    twitter_api: TwitterApiSettings
