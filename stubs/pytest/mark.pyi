from typing import Any, Callable, Iterable, Optional, TypeVar, Union

F = TypeVar('F', bound=Callable[..., Any])


def parametrize(argnames: str,
                argvalues: Iterable[Any],
                indirect: bool = False,
                ids: Optional[Union[Iterable[str], Callable[..., str]]] = None,
                scope: Optional[str] = None) -> Callable[..., F]:
    ...
