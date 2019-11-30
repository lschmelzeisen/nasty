from typing import Any, Callable, TypeVar

F = TypeVar('F', bound=Callable[..., Any])


def overrides(func: F) -> F:
    ...
