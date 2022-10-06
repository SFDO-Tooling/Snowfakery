import contextlib
from typing import Callable, ContextManager, Iterator, TypeVar

T = TypeVar("T")

# until https://github.com/agronholm/typeguard/issues/115 is fully fixed
# or typeguard is removed, we need this hack.

# The fix is on typeguard/master and should be merged in Typeguard 3.0
#
# We need this feature to be moved from UNRELEASED to RELEASED:
#
#    Changed the import hook to append @typechecked to the
#    decorator list instead of inserting it as the first decorator
#   (fixes type checking inconsistencies with mypy regarding at least
#    @contextmanager, probably others too)


def contextmanager(
    func: Callable[..., Iterator[T]]
) -> Callable[..., ContextManager[T]]:
    result = contextlib.contextmanager(func)
    result.__annotations__ = {**func.__annotations__, "return": ContextManager[T]}
    return result
