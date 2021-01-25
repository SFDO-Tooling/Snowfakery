#!/usr/bin/env python3
from snowfakery.generate_mapping_from_recipe import mapping_from_recipe_templates
from snowfakery.output_streams import (
    DebugOutputStream,
    SqlOutputStream,
    JSONOutputStream,
    CSVOutputStream,
    ImageOutputStream,
    GraphvizOutputStream,
    MultiplexOutputStream,
)
from snowfakery.data_gen_exceptions import DataGenError
from snowfakery.data_generator import generate, StoppingCriteria

import sys
from pathlib import Path
from contextlib import contextmanager

import yaml
import click
from snowfakery import version

if __name__ == "__main__":  # pragma: no cover
    sys.path.append(str(Path(__file__).parent.parent))


graphic_file_extensions = [
    "PNG",
    "png",
    "SVG",
    "svg",
    "svgz",
    "jpeg",
    "jpg",
    "ps",
    "dot",
]

file_extensions = [
    "JSON",
    "json",
    "txt",
    "csv",
] + graphic_file_extensions


def eval_arg(arg):
    if arg.isnumeric():
        return int(float(arg))
    else:
        return arg


# don't add a type signature to this function.
# typeguard and click will interfere with each other.
def int_string_tuple(ctx, param, value=None):
    """
    Parse a pair of strings that represent a string and a number.

    Either number, string or string, number is allowed as input."""
    if not value:
        return None
    assert len(value) == 2

    try:
        number, string = int(value[0]), value[1]
    except ValueError:
        try:
            string, number = value[0], int(value[1])
        except ValueError:
            raise click.BadParameter(
                "This parameter must be of the form 'number Name'. For example '50 Account'"
            )
    return string, number


@click.command()
# TODO: This should become type=click.File("r")
#       For consistency and flexibility
@click.argument("yaml_file", type=click.Path(exists=True))
@click.option(
    "--dburl",
    "dburls",
    type=str,
    multiple=True,
    help="URL for database to save data to. "
    "Use sqlite:///foo.db if you don't have one set up.",
)
@click.option("--output-format", "output_format", type=click.Choice(file_extensions))
@click.option("--output-folder", "output_folder", type=click.Path(), default=".")
@click.option("--output-file", "-o", "output_files", type=click.Path(), multiple=True)
@click.option(
    "--option",
    nargs=2,
    type=eval_arg,  # TODO: test this more
    multiple=True,
    help="Options to send to the recipe YAML.",
)
@click.option(
    "--target-number",
    nargs=2,
    help="Target options for the recipe YAML in the form of 'number tablename'. For example: '50 Account'.",
    callback=int_string_tuple,  # noqa  https://github.com/pallets/click/issues/789#issuecomment-535121714
)
@click.option(
    "--debug-internals/--no-debug-internals", "debug_internals", default=False
)
@click.option("--cci-mapping-file", "mapping_file", type=click.Path(exists=True))
@click.option(
    "--generate-cci-mapping-file",
    type=click.File("w"),
    help="Generate a CumulusCI mapping file for the dataset",
)
@click.option(
    "--generate-continuation-file",
    type=click.File("w"),
    help="A file that captures information about how to continue a "
    "multi-batch data generation process",
)
@click.option(
    "--continuation-file",
    type=click.File("r"),
    help="Continue generating a dataset where 'continuation-file' left off",
)
@click.version_option(version=version, prog_name="snowfakery")
def generate_cli(
    yaml_file,
    option=[],
    dburls=[],
    target_number=None,
    mapping_file=None,
    debug_internals=False,
    generate_cci_mapping_file=None,
    output_format=None,
    output_files=None,
    output_folder=None,
    continuation_file=None,
    generate_continuation_file=None,
):
    """
        Generates records from a YAML file

    \b
        Records can go to:
            * stdout (default)
            * JSON file (--output-format=json --output-file=foo.json)
            * diagram file (--output-format=png --output-file=foo.png)
            * a database identified by --dburl (e.g. --dburl sqlite:////tmp/foo.db)
            * or to a directory as a set of CSV files (--output-format=csv --output-folder=csvfiles)

        Diagram output depends on the installation of graphviz (https://www.graphviz.org/download/)

        Full documentation here:

            * https://snowfakery.readthedocs.io/en/docs/
    """
    output_files = list(output_files) if output_files else []
    stopping_criteria = stopping_criteria_from_target_number(target_number)
    output_format = output_format.lower() if output_format else None
    validate_options(
        yaml_file,
        option,
        dburls,
        mapping_file,
        debug_internals,
        generate_cci_mapping_file,
        output_format,
        output_files,
        output_folder,
    )
    with configure_output_stream(
        dburls, mapping_file, output_format, output_files, output_folder
    ) as output_stream:
        try:
            with click.open_file(yaml_file) as f:
                summary = generate(
                    open_yaml_file=f,
                    user_options=dict(option),
                    output_stream=output_stream,
                    stopping_criteria=stopping_criteria,
                    generate_continuation_file=generate_continuation_file,
                    continuation_file=continuation_file,
                )
            if debug_internals:
                debuginfo = yaml.dump(
                    summary.summarize_for_debugging(), sort_keys=False
                )
                sys.stderr.write(debuginfo)
            if generate_cci_mapping_file:
                yaml.safe_dump(
                    mapping_from_recipe_templates(summary),
                    generate_cci_mapping_file,
                    sort_keys=False,
                )
        except DataGenError as e:
            if debug_internals:
                raise e
            else:
                click.echo("")
                click.echo(e.prefix)
                raise click.ClickException(str(e)) from e


@contextmanager
def configure_output_stream(
    dburls, mapping_file, output_format, output_files, output_folder
):
    assert isinstance(output_files, (list, type(None)))
    output_streams = []  # we allow multiple output streams

    for dburl in dburls:
        if mapping_file:
            with click.open_file(mapping_file, "r") as f:
                mappings = yaml.safe_load(f)
        else:
            mappings = None

        output_streams.append(SqlOutputStream.from_url(dburl, mappings))

    # JSON is the only output format (other than debug) that can go on stdout
    if output_format == "json" and not output_files:
        output_streams.append(JSONOutputStream(sys.stdout))

    if output_format == "csv":
        output_streams.append(CSVOutputStream(output_folder))

    if output_files:
        for path in output_files:
            if output_folder:
                path = Path(output_folder, path)  # put the file in the output folder
            format = output_format or Path(path).suffix[1:]

            if format == "json":
                output_streams.append(JSONOutputStream(path))
            elif format == "txt":
                output_streams.append(DebugOutputStream(path))
            elif format == "dot":
                output_streams.append(GraphvizOutputStream(path))
            elif format in graphic_file_extensions:
                output_streams.append(ImageOutputStream(path, format))
            else:
                raise click.ClickException(
                    f"Unknown format or file extension: {format}"
                )

    if len(output_streams) == 0:
        output_stream = DebugOutputStream()
    elif len(output_streams) == 1:
        output_stream = output_streams[0]
    else:
        output_stream = MultiplexOutputStream(output_streams)
    try:
        yield output_stream
    finally:
        for output_stream in output_streams:
            try:
                messages = output_stream.close()
            except Exception as e:
                messages = None
                click.echo(f"Could not close {output_stream}: {str(e)}", err=True)
            if messages:
                for message in messages:
                    click.echo(message)


def validate_options(
    yaml_file,
    option,
    dburl,
    mapping_file,
    debug_internals,
    generate_cci_mapping_file,
    output_format,
    output_files,
    output_folder,
):
    if dburl and output_format:
        raise click.ClickException(
            "Sorry, you need to pick --dburl or --output-format "
            "because they are mutually exclusive."
        )
    if dburl and output_files:
        raise click.ClickException(
            "Sorry, you need to pick --dburl or --output-file "
            "because they are mutually exclusive."
        )
    if not dburl and mapping_file:
        raise click.ClickException("--cci-mapping-file can only be used with --dburl")
    if (
        output_folder
        and str(output_folder) != "."
        and not (output_files or output_format == "csv")
    ):
        raise click.ClickException(
            "--output-folder can only be used with --output-file=<something> or --output-format=csv"
        )


def stopping_criteria_from_target_number(target_number):
    "Deconstruct a tuple of 'str number' or 'number str' and make a StoppingCriteria"

    # 'number str' is the official format so the other one can be deprecated one day.
    if target_number:
        if isinstance(target_number[0], int):
            target_number = target_number[1], target_number[0]
        return StoppingCriteria(*target_number)

    return None


def main():
    generate_cli.main(prog_name="snowfakery")


if __name__ == "__main__":  # pragma: no cover
    main()
