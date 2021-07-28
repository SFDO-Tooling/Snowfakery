from pathlib import Path
from contextlib import contextmanager, ExitStack
import typing as T
import sys

import yaml
from click.utils import LazyFile

from snowfakery.data_generator import generate

from snowfakery.output_streams import (
    DebugOutputStream,
    MultiplexOutputStream,
    SqlDbOutputStream,
)
from snowfakery.generate_mapping_from_recipe import mapping_from_recipe_templates
from snowfakery.salesforce import create_cci_record_type_tables
from snowfakery.cci_mapping_files.declaration_parser import (
    SObjectRuleDeclarationFile,
    unify,
)
import snowfakery.data_gen_exceptions as exc
from snowfakery.data_generator_runtime import (
    StoppingCriteria,
)

OpenFileLike = T.Union[T.TextIO, LazyFile]
FileLike = T.Union[OpenFileLike, Path, str]

OUTPUT_FORMATS = {
    "png": "snowfakery.output_streams.ImageOutputStream",
    "svg": "snowfakery.output_streams.ImageOutputStream",
    "svgz": "snowfakery.output_streams.ImageOutputStream",
    "jpeg": "snowfakery.output_streams.ImageOutputStream",
    "jpg": "snowfakery.output_streams.ImageOutputStream",
    "ps": "snowfakery.output_streams.ImageOutputStream",
    "dot": "snowfakery.output_streams.GraphvizOutputStream",
    "json": "snowfakery.output_streams.JSONOutputStream",
    "txt": "snowfakery.output_streams.DebugOutputStream",
    "csv": "snowfakery.output_streams.CSVOutputStream",
    "sql": "snowfakery.output_streams.SqlTextOutputStream",
}

file_extensions = tuple(OUTPUT_FORMATS.keys())

COUNT_REPS = "__REPS__"


class SnowfakeryApplication:
    """Base class for all applications which embed Snowfakery as a library,
    including the Snowfakery CLI and CumulusCI"""

    stopping_criteria = None
    starting_id = 0
    rep_count = 0

    def __init__(self, stopping_criteria: StoppingCriteria = None):
        self.stopping_criteria = stopping_criteria or StoppingCriteria(COUNT_REPS, 1)

    def echo(self, message=None, file=None, nl=True, err=False, color=None):
        """Write something to a virtual stdout or stderr.

        Arguments to this function are derived from click.echo"""
        import click

        click.echo(message, file, nl, err, color)

    @property
    def stopping_tablename(self):
        """Return the name of "stopping table/object":

        The table/object whose presence determines
        whether we are done generating data.

        This is used by Snowfakery to validate that
        the provided recipe will not generate forever
        due to a misspelling the stopping tablename."""
        if self.stopping_criteria.tablename != COUNT_REPS:
            return self.stopping_criteria.tablename

    def ensure_progress_was_made(self, id_manager):
        """Check that we are actually making progress towards our goal"""
        if not self.stopping_tablename:
            return False

        last_used_id = id_manager[self.stopping_tablename]

        if last_used_id == self.starting_id:
            raise RuntimeError(
                f"{self.stopping_tablename} max ID was {self.starting_id} "
                f"before evaluating recipe and is {last_used_id} after. "
                f"At this rate we will never hit our target!"
            )

        self.starting_id = last_used_id

    def check_if_finished(self, id_manager):
        "Check whether we've finished making as many objects as we promised"
        # if nobody told us how much to make, finish after first run
        self.rep_count += 1

        target_table, count = self.stopping_criteria

        if target_table == COUNT_REPS:
            return self.rep_count >= count

        # Snowfakery processes can be restarted. We would need
        # to keep track of where we restarted to know whether
        # we are truly finished
        start = id_manager.start_ids.get(target_table, 1)
        target_id = start + count - 1

        last_used_id = id_manager[target_table]

        return last_used_id >= target_id


def stopping_criteria_from_target_number(target_number):
    "Deconstruct a tuple of 'str number' or 'number str' and make a StoppingCriteria"

    # 'number str' is the official format so the other one can be deprecated one day.
    if target_number:
        if isinstance(target_number[0], int):
            target_number = target_number[1], target_number[0]
        return StoppingCriteria(*target_number)

    return None


# Entry point to Snowfakery used by both the API ("snowfakery.generate_data")
# and the command line ("snowfakery.cli")
def generate_data(
    yaml_file: FileLike,
    *,
    parent_application: SnowfakeryApplication = None,  # the parent application
    user_options: T.Dict[str, str] = None,  # same as --option
    dburl: str = None,  # same as --dburl
    dburls=[],  # same as multiple --dburl options
    target_number: T.Tuple = None,  # same as --target-number
    debug_internals: bool = None,  # same as --debug-internals
    generate_cci_mapping_file: FileLike = None,  # same as --generate-cci-mapping-file
    output_format: str = None,  # same as --output-format
    output_file: FileLike = None,  # same as --output-file
    output_files: T.List[FileLike] = None,  # same as multiple --output-file options
    output_folder: FileLike = None,  # same as --output-folder
    continuation_file: FileLike = None,  # continuation file from last execution
    generate_continuation_file: FileLike = None,  # place to generate continuation file
    should_create_cci_record_type_tables: bool = False,  # create CCI Record type tables?
    load_declarations: T.Sequence[
        FileLike
    ] = None,  # read these load declarations for CCI
    plugin_options: T.Mapping = None,
) -> None:
    stopping_criteria = stopping_criteria_from_target_number(target_number)
    dburls = dburls or ([dburl] if dburl else [])
    output_files = output_files or []
    if output_file:
        output_files = output_files + [output_file]

    with ExitStack() as exit_stack:

        def open_with_cleanup(file, mode):
            return exit_stack.enter_context(open_file_like(file, mode))

        parent_application = parent_application or SnowfakeryApplication(
            stopping_criteria
        )

        output_stream = exit_stack.enter_context(
            configure_output_stream(
                dburls, output_format, output_files, output_folder, parent_application
            )
        )

        yaml_path, open_yaml_file = open_with_cleanup(yaml_file, "r")
        _, open_new_continue_file = open_with_cleanup(generate_continuation_file, "w")
        _, open_continuation_file = open_with_cleanup(continuation_file, "r")
        _, open_cci_mapping_file = open_with_cleanup(generate_cci_mapping_file, "w")

        summary = generate(
            open_yaml_file=open_yaml_file,
            user_options=user_options,
            output_stream=output_stream,
            parent_application=parent_application,
            generate_continuation_file=open_new_continue_file,
            continuation_file=open_continuation_file,
            stopping_criteria=stopping_criteria,
            plugin_options=plugin_options,
        )

        # This feature seems seldom useful. Delete it if it isn't missed
        # by fall 2021:

        # if debug_internals:
        #     debuginfo = yaml.dump(summary.summarize_for_debugging(), sort_keys=False)
        #     sys.stderr.write(debuginfo)

        if open_cci_mapping_file:
            declarations = gather_declarations(yaml_path or "", load_declarations)
            yaml.safe_dump(
                mapping_from_recipe_templates(summary, declarations),
                open_cci_mapping_file,
                sort_keys=False,
            )
    if should_create_cci_record_type_tables:
        create_cci_record_type_tables(dburls[0])


@contextmanager
def configure_output_stream(
    dburls, output_format, output_files, output_folder, parent_application
):
    assert isinstance(output_files, (list, type(None)))

    with _get_output_streams(
        dburls, output_files, output_format, output_folder
    ) as output_streams:
        if len(output_streams) == 0:
            output_stream = DebugOutputStream()
        elif len(output_streams) == 1:
            output_stream = output_streams[0]
        else:
            output_stream = MultiplexOutputStream(output_streams)
        try:
            yield output_stream
        finally:
            try:
                messages = output_stream.close()
            except Exception as e:
                messages = None
                parent_application.echo(
                    f"Could not close {output_stream}: {str(e)}", err=True
                )
            if messages:
                for message in messages:
                    parent_application.echo(message)


@contextmanager
def _get_output_streams(dburls, output_files, output_format, output_folder):
    with ExitStack() as onexit:
        output_streams = []  # we allow multiple output streams
        for dburl in dburls:
            output_streams.append(SqlDbOutputStream.from_url(dburl))

        if output_format and not output_files:
            output_stream_cls = get_output_stream_class(output_format)

            if output_stream_cls.is_text and not output_files:
                output_streams.append(output_stream_cls(sys.stdout))

            if output_stream_cls.uses_folder:
                output_streams.append(output_stream_cls(output_folder))

        if output_files:
            for f in output_files:
                format = output_format
                if output_folder and isinstance(f, (str, Path)):
                    f = Path(output_folder, f)  # put the file in the output folder
                file_context = open_file_like(f, "w")
                path, open_file = onexit.enter_context(file_context)
                if path and not format:
                    format = Path(path).suffix[1:].lower()

                if not format:
                    raise exc.DataGenError("No format supplied or inferrable")

                output_stream_cls = get_output_stream_class(format)
                if output_stream_cls.uses_path:
                    open_file.close()
                    open_file = path
                output_streams.append(output_stream_cls(open_file, format=format))

        yield output_streams


def get_output_stream_class(output_format):
    from snowfakery.plugins import resolve_plugin_alternatives, plugin_path

    if "." in output_format:
        output_stream_classname = output_format
    else:
        output_format = output_format.lower() if output_format else None
        output_stream_classname = OUTPUT_FORMATS.get(output_format)
    if not output_stream_classname:
        raise exc.DataGenError(f"Unknown format or file extension: {output_format}")
    with plugin_path([]):
        rc = resolve_plugin_alternatives(output_stream_classname)
    if not rc:
        raise exc.DataGenError(f"Cannot load {output_stream_classname}")
    return rc


def gather_declarations(yaml_file, load_declarations):
    """Gather declarations from load declaration files."""
    if not load_declarations:
        inferred_load_file_path = infer_load_file_path(yaml_file)
        if inferred_load_file_path.is_file():
            load_declarations = [inferred_load_file_path]

    if load_declarations:
        declarations = []
        for declfile in load_declarations:
            with open_file_like(declfile, "r") as (path, f):
                declarations.extend(SObjectRuleDeclarationFile.parse_from_yaml(f))

        unified_declarations = unify(declarations)
    else:
        unified_declarations = {}
    return unified_declarations


def infer_load_file_path(yaml_file: T.Union[str, Path]):
    """Infer a load declaration from a filename"""
    yaml_file = str(yaml_file)
    suffixes = "".join(Path(yaml_file).suffixes)
    if suffixes:
        return Path(yaml_file.replace(suffixes, ".load.yml"))
    else:
        return Path("")


@contextmanager
def open_file_like(
    file_like: T.Optional[FileLike], mode
) -> T.ContextManager[T.Tuple[str, OpenFileLike]]:
    if not file_like:
        yield None, None
    if isinstance(file_like, str):
        file_like = Path(file_like)

    if isinstance(file_like, Path):
        with file_like.open(mode) as f:
            yield file_like, f

    elif hasattr(file_like, "name"):
        yield file_like.name, file_like

    elif hasattr(file_like, "read"):
        yield None, file_like
