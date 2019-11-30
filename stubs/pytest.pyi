from typing import Any, Callable, Iterable, Optional, TypeVar, Union

_T_arg = TypeVar("_T_arg")
_T_func = TypeVar("_T_func", bound=Callable[..., Any])

class mark:  # noqa: N801
    @staticmethod
    def parametrize(
        argnames: str,
        argvalues: Iterable[_T_arg],
        indirect: bool = ...,
        ids: Optional[Union[Iterable[str], Callable[[_T_arg], str]]] = ...,
        scope: Optional[str] = ...,
    ) -> Callable[[_T_func], _T_func]: ...
