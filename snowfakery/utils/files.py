import typing as T
from contextlib import contextmanager
from pathlib import Path

from click.utils import LazyFile

OpenFileLike = T.Union[T.TextIO, LazyFile]
FileLike = T.Union[OpenFileLike, Path, str]


@contextmanager
def open_file_like(
    file_like: T.Optional[FileLike], mode, **kwargs
) -> T.ContextManager[T.Tuple[str, OpenFileLike]]:
    """Look at a file-like or path-like object and open it

    Returns a) the path it was given OR a best-guess of the path and
            b) the open file object

    Used properly as a context manager, it will close the file later
    if appropriate.
    """
    if not file_like:
        yield None, None
    if isinstance(file_like, str):
        file_like = Path(file_like)

    if isinstance(file_like, Path):
        with file_like.open(mode, **kwargs) as f:
            yield file_like, f

    elif hasattr(file_like, "name"):
        yield file_like.name, file_like

    elif hasattr(file_like, "read"):
        yield None, file_like
