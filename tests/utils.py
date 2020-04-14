from tempfile import TemporaryDirectory
from contextlib import contextmanager
from pathlib import Path


@contextmanager
def named_temporary_file_path(*, prefix="", suffix=""):
    """Context manager that yields a tempfile Path-like object

    Windows generally doesn't like files to be opened twice.
    Standard "NamedTemporaryFiles" are therefore of limited
    utility, because its hard to use them in a portable way."""

    with TemporaryDirectory() as d:
        yield Path(d) / (prefix + "tempfile" + suffix)
