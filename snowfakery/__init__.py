from pathlib import Path
from typing import Tuple, Union, Optional, Dict, TextIO, Sequence

from .plugins import SnowfakeryPlugin, lazy  # noqa
from .common_entry_point import generate_with_cci_features, EmbeddingContext

# TODO: when Python 3.6 is irrelevant, make this lazy:

# https://www.python.org/dev/peps/pep-0562/

version_file = Path(__file__).parent / "version.txt"
with version_file.open() as f:
    version = f.read().strip()


def generate_data(
    yaml_file: Union[Path, str],
    embedding_context: EmbeddingContext = None,
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
    should_create_cci_record_type_tables: bool = False,
    load_declarations: Sequence[Union[Path, str]] = None
):
    output_files = [output_file] if output_file else []

    return generate_with_cci_features(
        yaml_file=yaml_file,
        user_options=user_options,
        dburl=dburl,
        target_number=target_number,
        debug_internals=debug_internals,
        output_format=output_format,
        output_files=output_files,
        output_folder=output_folder,
        continuation_file=continuation_file,
        generate_continuation_file=generate_continuation_file,
        generate_cci_mapping_file=generate_cci_mapping_file,
        should_create_cci_record_type_tables=should_create_cci_record_type_tables,
        load_declarations=load_declarations,
    )
