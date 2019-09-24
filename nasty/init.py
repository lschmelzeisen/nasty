import sys
from logging import getLogger
from pathlib import Path
from typing import Dict

import toml

import nasty
from nasty.util.logging import setup_logging


def init_nasty() -> Dict:
    config = _load_config(get_source_folder() / 'config.toml')

    setup_logging(config['log_level'])
    _log_config(config)

    return config


def get_source_folder() -> Path:
    return Path(__file__).parent.parent


def _load_config(path: Path) -> Dict:
    if not path.exists():
        print('Could not find config file in "{}".'.format(path),
              file=sys.stderr)
        sys.exit()

    with path.open(encoding='UTF-8') as fin:
        config = toml.load(fin)

    return config


def _log_config(config: Dict):
    logger = getLogger(nasty.__name__)
    logger.debug('Loaded config:')
    for line in toml.dumps(config).splitlines():
        logger.debug('  ' + line)
