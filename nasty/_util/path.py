from contextlib import contextmanager
from pathlib import Path
from tempfile import NamedTemporaryFile, TemporaryDirectory

from overrides import overrides


@contextmanager
def TemporaryFilePath(*args, **kwargs):  # noqa: N802
    file = NamedTemporaryFile(*args, **kwargs, delete=False)
    path = Path(file.name)
    file.close()

    try:
        yield path
    finally:
        path.unlink()


class TemporaryDirectoryPath(TemporaryDirectory):
    @overrides
    def __enter__(self) -> Path:
        return Path(super().__enter__())
