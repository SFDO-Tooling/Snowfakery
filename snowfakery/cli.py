#!/usr/bin/env python3
from snowfakery.generate_mapping_from_factory import mapping_from_factory_templates
from snowfakery.output_streams import (
    DebugOutputStream,
    SqlOutputStream,
    JSONOutputStream,
    CSVOutputStream,
    ImageOutputStream,
    MultiplexOutputStream,
)
from snowfakery.data_gen_exceptions import DataGenError
from snowfakery.data_generator import generate, StoppingCriteria
import sys
from pathlib import Path
from typing import Tuple

import yaml
import click
from snowfakery.version import version

if __name__ == "__main__":  # pragma: no cover
    sys.path.append(str(Path(__file__).parent.parent))


file_extensions = [
    "JSON",
    "json",
    "PNG",
    "png",
    "SVG",
    "svg",
    "svgz",
    "jpeg",
    "jpg",
    "ps",
    "dot",
    "txt",
]


def eval_arg(arg):
    if arg.isnumeric():
        return int(float(arg))
    else:
        return arg


def string_int_tuple(ctx, param, value: Tuple[str, str] = None):
    """Works around Click bug

    https://github.com/pallets/click/issues/789#issuecomment-535121714"""
    if not value:
        return None
    else:
        return value[0], int(value[1])


@click.command()
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
@click.option("--output-file", "-o", "output_files", type=click.Path(), multiple=True)
@click.option(
    "--option",
    nargs=2,
    type=eval_arg,  # TODO: test this more
    multiple=True,
    help="Options to send to the factory YAML.",
)
@click.option(
    "--target-number",
    nargs=2,
    help="Target options for the factory YAML.",
    callback=string_int_tuple,  # noqa  https://github.com/pallets/click/issues/789#issuecomment-535121714
)
@click.option(
    "--debug-internals/--no-debug-internals", "debug_internals", default=False
)
@click.option("--cci-mapping-file", "mapping_file", type=click.Path(exists=True))
@click.option(
    "--generate-cci-mapping-file",
    "generate_cci_mapping_file",
    type=click.Path(exists=False),
)
@click.option(
    "--start-id",
    "start_ids",
    nargs=2,
    type=eval_arg,
    multiple=True,
    help="A pair that represents a table name and a number of rows to generate",
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
    start_ids=None,
    nickname_ids=None,
    continuation_file=None,
    generate_continuation_file=None,
):
    """
    Generates records from a YAML file

\b
    Records can go to:
        * stdout (default)
        * JSON file (--output_format=json --output-file=foo.json)
        * diagram file (--output_format=png --output-file=foo.png)
        * a database identified by --dburl (e.g. --dburl sqlite:////tmp/foo.db)
        * or to a directory as a set of CSV files (--dburl csvfile:///directory/)

    Diagram output depends on the installation of pygraphviz ("pip install pygraphviz")
    """
    output_files = list(output_files) if output_files else []
    start_ids = list(start_ids) if start_ids else []
    stopping_criteria = StoppingCriteria(*target_number) if target_number else None
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
    )
    output_stream = configure_output_stream(
        dburls, mapping_file, output_format, output_files
    )

    try:
        assert output_stream
        with click.open_file(yaml_file) as f:
            summary = generate(
                open_yaml_file=f,
                user_options=dict(option),
                output_stream=output_stream,
                stopping_criteria=stopping_criteria,
                generate_continuation_file=generate_continuation_file,
                continuation_file=continuation_file,
            )
        output_stream.close()
        if debug_internals:
            debuginfo = yaml.dump(summary.summarize_for_debugging(), sort_keys=False)
            sys.stdout.write(debuginfo)
        if generate_cci_mapping_file:
            with click.open_file(generate_cci_mapping_file, "w") as f:
                yaml.safe_dump(
                    mapping_from_factory_templates(summary), f, sort_keys=False
                )
    except DataGenError as e:
        if debug_internals:
            raise e
        else:
            click.echo("")
            click.echo(
                "An error occurred. If you would like to see a Python traceback, "
                "use the --debug-internals option."
            )
            raise click.ClickException(str(e)) from e
    finally:
        ...
        # TODO: close output streams


def configure_output_stream(dburls, mapping_file, output_format, output_files):
    assert isinstance(output_files, (list, type(None)))
    output_streams = []  # we allow multiple output streams

    for dburl in dburls:
        if mapping_file:
            with click.open_file(mapping_file, "r") as f:
                mappings = yaml.safe_load(f)
        else:
            mappings = None
        if dburl.startswith("csvfile:/"):
            output_streams.append(CSVOutputStream(dburl))
        else:
            output_streams.append(SqlOutputStream.from_url(dburl, mappings))

    # JSON is the only output format (other than debug) that can go on stdout
    if output_format == "json" and not output_files:
        output_streams.append(JSONOutputStream(click.open_file("-", "w")))

    if output_files:
        for path in output_files:
            format = output_format or Path(path).suffix[1:]

            if format == "json":
                output_streams.append(JSONOutputStream(click.open_file(path, "w")))
            elif format == "txt":
                output_streams.append(DebugOutputStream(click.open_file(path, "w")))
            else:
                output_streams.append(
                    ImageOutputStream(click.open_file(path, "wb"), format)
                )

    if len(output_streams) == 0:
        output_stream = DebugOutputStream()
    elif len(output_streams) == 1:
        output_stream = output_streams[0]
    else:
        output_stream = MultiplexOutputStream(output_streams)
    return output_stream


def validate_options(
    yaml_file,
    option,
    dburl,
    mapping_file,
    debug_internals,
    generate_cci_mapping_file,
    output_format,
    output_files,
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
        raise click.ClickException("Mapping file can only be used with --dburl")


def main():
    generate_cli.main(prog_name="snowfakery")


if __name__ == "__main__":  # pragma: no cover
    main()
