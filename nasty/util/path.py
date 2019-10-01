from pathlib import Path
from tempfile import NamedTemporaryFile, TemporaryDirectory


class TemporaryFilePath:
    def __init__(self, *args, **kwargs):
        self.file = NamedTemporaryFile(*args, **kwargs, delete=False)
        self.path = Path(self.file.name)
        self.file.close()

    def __enter__(self) -> Path:
        return self.path

    def __exit__(self, *args, **kwargs) -> None:
        self.path.unlink()


class TemporaryDirectoryPath(TemporaryDirectory):
    def __enter__(self) -> Path:
        return Path(super().__enter__())
