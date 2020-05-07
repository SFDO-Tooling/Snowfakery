import warnings
from typing import IO, Tuple, Mapping, List, Dict, TextIO, Union
from importlib import import_module
from click.utils import LazyFile

from yaml import safe_dump, safe_load
from faker.providers import BaseProvider as FakerProvider

from .data_gen_exceptions import DataGenNameError
from .output_streams import (
    DebugOutputStream,
    OutputStream,
)
from .parse_factory_yaml import parse_factory
from .data_generator_runtime import output_batches, StoppingCriteria, Globals
from . import SnowfakeryPlugin


# This tool is essentially a three stage interpreter.
#
# 1. Yaml parsing into Python data structures.
# 2. Walking the tree, sorting things into groups like macros, file inclusions,
#    etc., and doing the file inclusions (parse_factory_yaml.parse_factory)
# 2 a) merge options informtion from the parse with options from the
#      environment
# 3. Generating the objects top to bottom (including evaluating Jinja) in
#    data_generator_runtime.output_batches
#
# The function generate at the bottom of this file is the entry point to all
# of it.


class ExecutionSummary:
    """Summarize everything that happened during parsing and evaluating."""

    def __init__(self, parse_results, runtime_results):
        self.tables = parse_results.tables
        self.templates = parse_results.templates
        self.intertable_dependencies = runtime_results.intertable_dependencies

    def summarize_for_debugging(self):
        return self.intertable_dependencies, self.templates


def merge_options(option_definitions: List, user_options: Mapping) -> Tuple[Dict, set]:
    """Merge/compare options specified by end-user to those declared in YAML file.

    Takes options passed in from the command line or a config file and
    compare them to the options declared by the Generator YAML file.

    The options from the Generator YAML should be dictionaries with keys of
    "options" and "default" as described in the user documentation.

    The options from the user should be a dictionary of key/value pairs.

    The output is a pair, options, extra_options. The options are the values
    to be fed into the process after applying defaults.

    extra_options are options that the user specified which do not match
    anything in the YAML generator file. The caller may want to warn the
    user about them or throw an error.
    """
    options = {}
    for option in option_definitions:
        name = option["option"]
        if user_options.get(name):
            options[name] = user_options.get(name)
        elif option.get("default"):
            options[name] = option["default"]
        else:
            raise DataGenNameError(
                f"No definition supplied for option {name}", None, None
            )

    extra_options = set(user_options.keys()) - set(options.keys())
    return options, extra_options


def load_continuation_yaml(continuation_file: TextIO):
    """Load a continuation file from YAML."""
    return safe_load(continuation_file)


def save_continuation_yaml(continuation_data: Globals, continuation_file: TextIO):
    safe_dump(continuation_data, continuation_file)


def resolve_plugin(plugin: str) -> object:
    "Resolve a plugin to a class"
    module_name, class_name = plugin.rsplit(".", 1)
    module = import_module(module_name)
    cls = getattr(module, class_name)
    if issubclass(cls, FakerProvider):
        return (FakerProvider, cls)
    elif issubclass(cls, SnowfakeryPlugin):
        return (SnowfakeryPlugin, cls)
    else:
        raise TypeError(f"{cls} is not a Faker Provider nor Snowfakery Plugin")


def process_plugins(plugins: List[str]) -> Tuple[List[object], Mapping[str, object]]:
    """Resolve a list of names for SnowfakeryPlugins and Faker Providers to objects

    The Providers are returned as a list of objects.
    The Plugins are a mapping of ClassName:object so they can be namespaced.
    """
    plugin_classes = [resolve_plugin(plugin) for plugin in plugins]
    faker_providers = [
        provider for baseclass, provider in plugin_classes if baseclass == FakerProvider
    ]
    snowfakery_plugins = {
        plugin.__name__: plugin
        for baseclass, plugin in plugin_classes
        if baseclass == SnowfakeryPlugin
    }
    return (faker_providers, snowfakery_plugins)


def generate(
    open_yaml_file: IO[str],
    user_options: dict = None,
    output_stream: OutputStream = None,
    stopping_criteria: StoppingCriteria = None,
    generate_continuation_file: Union[TextIO, LazyFile] = None,
    continuation_file: TextIO = None,
) -> ExecutionSummary:
    """The main entry point to the package for Python applications."""
    user_options = user_options or {}

    # Where are we going to put the rows?
    output_stream = output_stream or DebugOutputStream()

    # parse the YAML and any it refers to
    parse_result = parse_factory(open_yaml_file)

    # figure out how it relates to CLI-supplied generation variables
    options, extra_options = merge_options(parse_result.options, user_options)

    if extra_options:
        warnings.warn(f"Warning: unknown options: {extra_options}")

    output_stream.create_or_validate_tables(parse_result.tables)

    continuation_data = (
        load_continuation_yaml(continuation_file) if continuation_file else None
    )

    faker_providers, snowfakery_plugins = process_plugins(parse_result.plugins)

    # now do the output
    runtime_context = output_batches(
        output_stream,
        parse_result.templates,
        options,
        stopping_criteria=stopping_criteria,
        continuation_data=continuation_data,
        tables=parse_result.tables,
        snowfakery_plugins=snowfakery_plugins,
        faker_providers=faker_providers,
    )

    if generate_continuation_file:
        safe_dump(runtime_context, generate_continuation_file)

    return ExecutionSummary(parse_result, runtime_context)


if __name__ == "__main__":  # pragma: no cover
    from .snowfakery import generate_cli

    generate_cli()
