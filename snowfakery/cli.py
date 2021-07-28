#!/usr/bin/env python3
import sys
from pathlib import Path

from snowfakery.data_gen_exceptions import DataGenError


import click
from snowfakery import version
from snowfakery.api import file_extensions, generate_data, COUNT_REPS

if __name__ == "__main__":  # pragma: no cover
    sys.path.append(str(Path(__file__).parent.parent))


class FormatChoice(click.Choice):
    def convert(self, value, param, ctx):
        if isinstance(value, str) and "." in value:
            return value

        return super().convert(value, param, ctx)


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
@click.argument("yaml_file", type=click.File("r"))
@click.option(
    "--dburl",
    "dburls",
    type=str,
    multiple=True,
    help="URL for database to save data to. "
    "Use sqlite:///foo.db if you don't have one set up.",
)
@click.option(
    "--output-format",
    "output_format",
    type=FormatChoice(file_extensions, case_sensitive=False),
)
@click.option("--output-folder", "output_folder", type=click.Path(), default=".")
@click.option("--output-file", "-o", "output_files", type=click.Path(), multiple=True)
@click.option(
    "--option",
    nargs=2,
    type=eval_arg,
    multiple=True,
    help="Option to send to the recipe YAML in a format like 'OptName OptValue'. Specify multiple times if needed.",
)
@click.option(
    "--target-number",
    "--target-count",
    nargs=2,
    help="Target record count for the recipe YAML in the form of 'number tablename'. "
    "For example: '50 Account' to generate roughly 50 accounts.",
    callback=int_string_tuple,  # noqa  https://github.com/pallets/click/issues/789#issuecomment-535121714
)
@click.option(
    "--reps",
    help="Target repetition count for the recipe YAML. Use as an alternative to --target-number",
    type=int,
)
@click.option(
    "--debug-internals/--no-debug-internals", "debug_internals", default=False
)
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
    "--generate-record-type-tables/--no-generate-record-type-tables",
    "should_create_cci_record_type_tables",
    default=False,
    hidden=True,
)
@click.option(
    "--continuation-file",
    type=click.File("r"),
    help="Continue generating a dataset where 'continuation-file' left off",
)
@click.option(
    "--plugin-option",
    nargs=2,
    type=eval_arg,
    multiple=True,
    help="Option to send to a plugin in a format like 'OptName OptValue'. Specify multiple times if needed.",
)  # options passed by an API instead of CLI
@click.option(
    "--load-declarations",
    type=click.Path(exists=True, readable=True, dir_okay=False),
    help="Declarations to mix into the generated mapping file",
    multiple=True,
)
@click.version_option(version=version, prog_name="snowfakery")
def generate_cli(
    yaml_file,
    option=(),
    dburls=(),
    target_number=None,
    reps=None,
    debug_internals=None,
    generate_cci_mapping_file=None,
    output_format=None,
    output_files=None,
    output_folder=None,
    continuation_file=None,
    generate_continuation_file=None,
    plugin_option=(),
    should_create_cci_record_type_tables=False,
    load_declarations=None,
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
    validate_options(
        yaml_file,
        option,
        dburls,
        debug_internals,
        generate_cci_mapping_file,
        output_format,
        output_files,
        output_folder,
        target_number,
        reps,
    )
    try:
        user_options = dict(option)
        plugin_options = dict(plugin_option)
        if reps:
            target_number = (COUNT_REPS, reps)

        generate_data(
            yaml_file=yaml_file,
            user_options=user_options,
            dburls=dburls,
            target_number=target_number,
            debug_internals=debug_internals,
            generate_cci_mapping_file=generate_cci_mapping_file,
            output_format=output_format,
            output_files=output_files,
            output_folder=output_folder,
            continuation_file=continuation_file,
            generate_continuation_file=generate_continuation_file,
            should_create_cci_record_type_tables=should_create_cci_record_type_tables,
            load_declarations=load_declarations,
            plugin_options=plugin_options,
        )
    except DataGenError as e:
        if debug_internals:
            raise e
        else:
            click.echo("")
            click.echo(e.prefix)
            raise click.ClickException(str(e)) from e


def validate_options(
    yaml_file,
    option,
    dburl,
    debug_internals,
    generate_cci_mapping_file,
    output_format,
    output_files,
    output_folder,
    target_number,
    reps,
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
    if (
        output_folder
        and str(output_folder) != "."
        and not (output_files or output_format == "csv")
    ):
        raise click.ClickException(
            "--output-folder can only be used with --output-file=<something> or --output-format=csv"
        )

    if target_number and reps:
        raise click.ClickException(
            "Sorry, you need to pick --target_number or --reps "
            "because they are mutually exclusive."
        )


def main():
    generate_cli.main(prog_name="snowfakery")


if __name__ == "__main__":  # pragma: no cover
    main()
