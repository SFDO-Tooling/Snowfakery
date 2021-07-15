import sys

from typing import Any, Callable, Mapping, Union, NamedTuple, List, Tuple
from importlib import import_module
from datetime import date, datetime
from pathlib import Path
from unittest.mock import patch

import yaml
from yaml.representer import Representer
from faker.providers import BaseProvider as FakerProvider

import snowfakery.data_gen_exceptions as exc
from .utils.yaml_utils import SnowfakeryDumper
from .utils.collections import CaseInsensitiveDict

from numbers import Number


Scalar = Union[str, Number, date, datetime, None]
FieldDefinition = "snowfakery.data_generator_runtime_object_model.FieldDefinition"


class LineTracker(NamedTuple):
    filename: str
    line_num: int


class SnowfakeryPlugin:
    """Base class for all plugins.

    Currently plugins can declare new functions. Over time new superpowers
    for plugins will be introduced.

    Plugins generally look like this:

    class MyPlugin:
        class Functions: # must be named `Functions`.
            def func1(self, arg1, arg2, arg3=default):
                return something()

    This function would be invoked through the name `MyPlugin.func1()`

    Despite the name, the Functions namespace could also include
    constants or other namespaces, if that is useful to you.

    A RuntimeContext object is supplied on `self.context` with methods
    context.field_vars() and context.context_vars().

    context.field_vars() are the same field variables that can be used in
    templates.

    context.context_vars() is a mutable mapping contaiing
    values that are available to this object template and that of
    all children.

    context_vars are unique to each plugin and plugins do not see
    (or corrupt, or overwrite) context_vars for another plugin.

    Plugins can also keep internal state for global data, like any other
    Python object.
    """

    def __init__(self, interpreter):
        self.interpreter = interpreter
        self.context = PluginContext(self)

    def custom_functions(self, *args, **kwargs):
        """Instantiate, contextualize and return a function library

        Default behaviour is to return self.Function()."""
        functions = self.Functions()
        functions.context = self.context
        return functions

    def close(self, *args, **kwargs):
        pass


class ParserMacroPlugin:
    """Abstract base class for plugins that generate code.

    Note that these are currently undocumented and their
    interface is not necessarily stable."""

    pass


class PluginContext:
    "Exposes certain stable internals to plugins"

    def __init__(self, plugin):
        self.plugin = plugin
        self.interpreter = plugin.interpreter

    def field_vars(self):
        return self.interpreter.current_context.field_vars()

    def context_vars(self):
        return self.interpreter.current_context.context_vars(
            self.plugin.__class__.__name__
        )

    def unique_context_identifier(self) -> str:
        "An identifier that will be unique across iterations (but not portion invocations)"
        return self.interpreter.current_context.unique_context_identifier

    def evaluate_raw(self, field_definition):
        """Evaluate the contents of a field definition"""
        return field_definition.render(self.interpreter.current_context)

    def evaluate(self, field_definition):
        """Evaluate the contents of a field definition and simplify to a primitive value."""
        rc = self.evaluate_raw(field_definition)
        if isinstance(rc, Scalar.__args__):
            return rc
        elif hasattr(rc, "simplify"):
            return rc.simplify()
        else:
            raise f"Cannot simplify {field_definition}. Perhaps should have used evaluate_raw?"

    @property
    def current_filename(self):
        return self.interpreter.current_context.current_template.filename


def lazy(func: Any) -> Callable:
    """A lazy function is one that expects its arguments to be unparsed"""
    func.lazy = True
    return func


def resolve_plugins(
    plugin_specs: List[Tuple[str, object]], search_paths: List[Union[str, Path]]
):
    "Resolve a list of plugins and lineinfos"
    with plugin_path(search_paths):
        plugins = []
        for plugin_spec in plugin_specs:
            plugins.extend(resolve_plugin(*plugin_spec))
        return plugins


def plugin_path(search_paths):
    cwd_plugins = "./plugins"
    user_plugins = Path.home() / ".snowfakery/plugins"
    new_sys_path = [
        *sys.path,
        *(str(p) for p in search_paths),
        str(cwd_plugins),
        str(user_plugins),
    ]
    return patch.object(sys, "path", new_sys_path)


def resolve_plugin(plugin: str, lineinfo) -> object:
    """Resolve a plugin to a class"""
    cls = resolve_plugin_alternatives(plugin)
    if not cls:
        raise exc.DataGenImportError(
            f"Cannot find plugin: {plugin}", lineinfo.filename, lineinfo.line_num
        )

    categories = []

    if issubclass(cls, FakerProvider):
        categories.append((FakerProvider, cls))
    else:
        if issubclass(cls, SnowfakeryPlugin):
            categories.append((SnowfakeryPlugin, cls))
        if issubclass(cls, ParserMacroPlugin):
            categories.append((ParserMacroPlugin, cls))

    if categories:
        return categories
    else:
        raise exc.DataGenTypeError(
            f"{cls} is not a Faker Provider nor Snowfakery Plugin",
            lineinfo.filename,
            lineinfo.line_num,
        )


def resolve_plugin_alternatives(plugin):
    """Interpret the plugin declaration in 2 ways.
    Return it when we find one that matches.

    1. The new way, which allows shorter declarations.
    2. The old way, which required everything to be spelled out.

    In other words:

    - plugin: foo.bar.Baz

    Means.

    1. The new way:

    from foo.bar.Baz import Baz

    2. The old way:

    from foo.bar import Baz
    """
    prefix, class_name = plugin.rsplit(".", 1)
    testnames = [plugin + "." + class_name, plugin]

    for testname in testnames:
        module_name, class_name = testname.rsplit(".", 1)
        try:
            module = import_module(module_name)
            if hasattr(module, class_name):
                assert getattr(module, class_name)
                return getattr(module, class_name)
        except ModuleNotFoundError:
            pass


class PluginResult:
    """`PluginResult` objects expose a namespace that other code can access through dot-notation.

    PluginResults can be initialized with a dict or dict-like object.

    PluginResults are serialized to continuation files as dicts."""

    def __init__(self, result: Mapping):
        self.result = CaseInsensitiveDict(result)

    def __getattr__(self, name):
        # ensures that it won't recurse
        return self.__dict__["result"][name]

    def __reduce__(self):
        return (self.__class__, (dict(self.result),))

    def __repr__(self):
        return f"<{self.__class__} {repr(self.result)}>"

    def __str__(self):
        return str(self.result)


class PluginOption:
    def __init__(self, name, typ):
        self.name = name
        self.type = typ

    def convert(self, value):
        try:
            return self.type(value)
        except TypeError as e:
            raise TypeError(
                f"{self.name} option is wrong type {type(value)} rather than {self.type}",
                *e.args,
            )


# round-trip PluginResult objects through continuation YAML if needed.
SnowfakeryDumper.add_representer(PluginResult, Representer.represent_object)
yaml.SafeLoader.add_constructor(
    "tag:yaml.org,2002:python/object/apply:snowfakery.plugins.PluginResult",
    lambda loader, node: PluginResult(loader.construct_sequence(node)[0]),
)
