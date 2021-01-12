from pathlib import Path
from typing import Tuple, Union, Optional, Dict, TextIO
from contextlib import ExitStack

from .plugins import SnowfakeryPlugin, lazy  # noqa


# TODO: when Python 3.6 is irrelevant, make this lazy:

# https://www.python.org/dev/peps/pep-0562/

version_file = Path(__file__).parent / "version.txt"
with version_file.open() as f:
    version = f.read().strip()


def generate_data(
    yaml_file: Union[Path, str],
    *,
    user_options: Dict[str, str] = None,
    dburl: str = None,
    target_number: Optional[Tuple[int, str]] = None,
    debug_internals: bool = False,
    output_format: str = None,
    output_file: Path = None,
    output_folder: Path = None,
    continuation_file: Path = None,
    generate_continuation_file: Union[TextIO, Path] = None,
    generate_cci_mapping_file: Union[TextIO, Path] = None,
):
    from .cli import generate_cli

    if target_number:
        assert isinstance(target_number[0], int)

    dburls = [dburl] if dburl else []
    output_files = [output_file] if output_file else []
    options_sequence = list(user_options.items()) if user_options else ()

    with ExitStack() as stack:

        def open_if_necessary_and_close_later(file_like, mode):
            if hasattr(file_like, "open"):
                file_like = file_like.open(mode)
                stack.enter_context(file_like)
            return file_like

        generate_continuation_file = open_if_necessary_and_close_later(
            generate_continuation_file, "w"
        )
        generate_cci_mapping_file = open_if_necessary_and_close_later(
            generate_cci_mapping_file, "w"
        )

        return generate_cli.callback(
            yaml_file=yaml_file,
            option=options_sequence,
            dburls=dburls,
            target_number=target_number,
            debug_internals=debug_internals,
            output_format=output_format,
            output_files=output_files,
            output_folder=output_folder,
            continuation_file=continuation_file,
            generate_continuation_file=generate_continuation_file,
            generate_cci_mapping_file=generate_cci_mapping_file,
        )
