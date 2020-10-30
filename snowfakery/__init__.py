from pathlib import Path
from typing import Tuple, List, Union, Optional

from .plugins import SnowfakeryPlugin, lazy  # noqa


# TODO: when Python 3.6 is irrelevant, make this lazy:

# https://www.python.org/dev/peps/pep-0562/

version_file = Path(__file__).parent / "version.txt"
with version_file.open() as f:
    version = f.read().strip()


def generate_data(
    yaml_file: Union[Path, str],
    option: List[Tuple[str, str]] = [],
    dburl: str = None,
    target_number: Optional[Tuple[int, str]] = None,
    debug_internals: bool = False,
    output_format: str = None,
    output_file: Path = None,
    output_folder: Path = None,
    continuation_file: Path = None,
):
    from .cli import generate_cli

    if target_number:
        assert isinstance(target_number[0], int)

    dburls = [dburl] if dburl else []
    output_files = [output_file] if output_file else []

    return generate_cli.callback(
        yaml_file=yaml_file,
        option=option,
        dburls=dburls,
        target_number=target_number,
        debug_internals=debug_internals,
        output_format=output_format,
        output_files=output_files,
        output_folder=output_folder,
        continuation_file=continuation_file,
    )
