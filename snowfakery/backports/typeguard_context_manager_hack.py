import contextlib
from typing import Callable, ContextManager, Iterator, TypeVar

T = TypeVar("T")


def contextmanager(
    func: Callable[..., Iterator[T]]
) -> Callable[..., ContextManager[T]]:
    result = contextlib.contextmanager(func)
    result.__annotations__ = {**func.__annotations__, "return": ContextManager[T]}
    return result
