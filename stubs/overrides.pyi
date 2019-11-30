from typing import Any, Callable, TypeVar

_T_func = TypeVar("_T_func", bound=Callable[..., Any])

def overrides(func: _T_func) -> _T_func: ...
