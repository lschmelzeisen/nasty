from pathlib import Path
from tempfile import TemporaryDirectory


class TemporaryDirectoryPath(TemporaryDirectory):
    def __enter__(self) -> Path:
        return Path(super().__enter__())
