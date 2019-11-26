import sys
from logging import getLogger
from pathlib import Path
from typing import Any, Dict

import toml

from nasty.util.logging import setup_logging


def init_nasty() -> Dict[str, Any]:
    config = _load_config(get_source_folder() / 'config.toml')

    setup_logging(config['log_level'])
    _log_config(config)

    return config


def get_source_folder() -> Path:
    return Path(__file__).parent.parent


def _load_config(path: Path) -> Dict[str, Any]:
    if not path.exists():
        print('Could not find config file in "{}". Make sure you copy the '
              'example config file to this location and set your personal '
              'settings/secrets.'.format(path), file=sys.stderr)
        sys.exit()

    with path.open(encoding='UTF-8') as fin:
        config = toml.load(fin)

    return config


def _log_config(config: Dict[str, Any]):
    def hide_secrets(value, hidden=False):
        if isinstance(value, dict):
            return {k: hide_secrets(v, hidden=(hidden or ('secret' in k)))
                    for k, v in value.items()}
        return '<hidden>' if hidden else value

    logger = getLogger(__name__)
    logger.debug('Loaded config:')
    for line in toml.dumps(hide_secrets(config)).splitlines():
        logger.debug('  ' + line)
