from collections import defaultdict
from functools import partial
from datetime import date

from typing import Optional, Dict, List, Sequence, Mapping, Any, NamedTuple

import jinja2
import yaml

from .utils.template_utils import FakerTemplateLibrary

from .template_funcs import template_funcs
from .data_gen_exceptions import DataGenSyntaxError, DataGenNameError
import snowfakery  # noqa

OutputStream = "snowfakery.output_streams.OutputStream"


# Runtime objects and algorithms used during the generation of rows.


class StoppingCriteria(NamedTuple):
    tablename: str
    count: int


class FinishedChecker:
    """Check whether the process is finished"""
    target_table_name: str = None
    target_id: int = None
    target_progress_id: int = 0

    def __init__(self, start_ids, stopping_criteria):
        """Ensure that the stopping criteria accounts for the start_ids"""
        if stopping_criteria:
            self.target_table_name, target_count = stopping_criteria
            if start_ids:
                start = start_ids.get(self.target_table_name, 1)
            else:
                start = 1
            self.target_id = start + target_count - 1

    def finished(self, id_manager):
        """Check whether we've finished making as many objects as we promised"""
        # if nobody told us how much to make, finish after first run
        if not self.target_table_name:
            return True

        last_used_id = id_manager[self.target_table_name]

        if last_used_id == self.target_progress_id:
            raise RuntimeError(
                f"{self.target_table_name} max ID was {self.target_progress_id} "
                f"before evaluating factory and is {last_used_id} after. "
                f"At this rate we will never hit our target of {self.target_id}!"
            )

        self.target_progress_id = last_used_id

        return last_used_id >= self.target_id


class IdManager(yaml.YAMLObject):
    """Keep track of the most recent ID per Object type"""

    yaml_loader = yaml.SafeLoader
    yaml_dumper = yaml.SafeDumper
    yaml_tag = "!snowfakery_ids"

    def __init__(self, start_ids: Optional[Dict[str, int]] = None):
        start_ids = start_ids or {}
        self.last_used_ids = defaultdict(lambda: 0)
        for name, value in start_ids.items():
            self.last_used_ids[name] = value - 1

    def generate_id(self, table_name: str) -> int:
        self.last_used_ids[table_name] += 1
        return self.last_used_ids[table_name]

    def __getitem__(self, table_name: str) -> int:
        return self.last_used_ids[table_name]

    def __setstate__(self, state):
        self.last_used_ids = defaultdict(lambda: 0, state["last_used_ids"])


yaml.SafeDumper.add_representer(defaultdict, yaml.SafeDumper.represent_dict)


class Dependency(NamedTuple):
    yaml_loader = yaml.SafeLoader
    yaml_dumper = yaml.SafeDumper
    yaml_tag = "!snowfakery_dependency"

    table_name_from: str
    table_name_to: str
    field_name: str


yaml.SafeDumper.add_representer(
    Dependency, lambda representer, obj: representer.represent_list(obj)
)


class Globals(yaml.YAMLObject):
    """Globally named objects and other aspects of global scope"""

    yaml_loader = yaml.SafeLoader
    yaml_dumper = yaml.SafeDumper
    yaml_tag = "!snowfakery_globals"

    def __init__(self, start_ids: Optional[Dict[str, id]] = None, today: date = None):
        self.named_objects = {}
        self.id_manager = IdManager(start_ids)
        self.last_seen_obj_of_type = {}
        self.intertable_dependencies = set()
        self.today = today or date.today()

    def register_object(self, obj, nickname: str = None):
        """Register an object for lookup by object type and (optionally) Nickname"""
        if nickname:
            self.named_objects[nickname] = obj
        self.last_seen_obj_of_type[obj._tablename] = obj

    @property
    def object_names(self):
        """The globally named objects"""
        return {**self.named_objects, **self.last_seen_obj_of_type}

    def register_intertable_reference(
        self, table_name_from: str, table_name_to: str, fieldname: str
    ):
        self.intertable_dependencies.add(
            Dependency(table_name_from, table_name_to, fieldname)
        )

    def __getstate__(self):
        state = self.__dict__.copy()
        del state["intertable_dependencies"]
        return state

    def __setstate__(self, state):
        self.last_seen_obj_of_type = {}
        for slot, value in state.items():
            setattr(self, slot, value)
        self.intertable_dependencies = set()


class JinjaTemplateEvaluatorFactory:
    def __init__(self):
        self.template_compiler = jinja2.Environment(
            block_start_string="<%",
            block_end_string="%>",
            variable_start_string="<<",
            variable_end_string=">>",
        )

    def get_evaluator(self, definition: str):
        assert isinstance(definition, str), definition
        if "<<" in definition or "<%" in definition:
            try:
                template = self.template_compiler.from_string(definition)
                return DynamicEvaluator(template)
            except jinja2.exceptions.TemplateSyntaxError as e:
                raise DataGenSyntaxError(str(e), None, None) from e
        else:
            return lambda context: definition


class RuntimeContext:
    """State of the interpreter. RuntimeContexts live on the Python stack."""

    current_id = None
    obj: Optional["ObjectRow"] = None
    template_evaluator_factory = JinjaTemplateEvaluatorFactory()

    def __init__(
        self,
        globaldata: Globals,
        current_table_name: Optional[str],
        faker_template_library: FakerTemplateLibrary,
        output_stream: OutputStream = None,
        options: Mapping = None,
        start_ids: Optional[Mapping[str, int]] = None,
        stopping_criteria: Optional[StoppingCriteria] = None,
        snowfakery_plugins: Optional[Mapping[str, callable]] = None,
    ):
        self.globals = globaldata
        self.current_table_name = current_table_name
        self.options = options or {}
        self.field_values: Dict[str, Any] = {}
        self.output_stream = output_stream
        self.faker_template_library = faker_template_library

        self.finished_checker = FinishedChecker(start_ids, stopping_criteria)

        self.snowfakery_plugins = snowfakery_plugins or {}
        # todo: some caching of these could speed things up a bit
        self.plugin_function_libraries = {
            name: plugin().custom_functions(self)
            for name, plugin in self.snowfakery_plugins.items()
        }

    def finished(self):
        return self.finished_checker.finished(self.globals.id_manager)

    def generate_id(self):
        return self.globals.id_manager.generate_id(self.current_table_name)

    def register_object(self, obj, name=None):
        self.obj = obj
        self.globals.register_object(obj, name)

    def register_intertable_reference(self, table_name_from, table_name_to, fieldname):
        self.globals.register_intertable_reference(
            table_name_from, table_name_to, fieldname
        )

    def register_field(self, field_name, field_value):
        """Register each field value to be ready to inject them into template"""
        self.field_values[field_name] = field_value

    def child_context(self, tablename):
        "Create a nested context (analogous to a 'stack frame')."
        return self.__class__(
            self.globals,
            tablename,
            self.faker_template_library,
            output_stream=self.output_stream,
            options=self.options,
            snowfakery_plugins=self.snowfakery_plugins,
        )

    def field_vars(self):
        return {
            "id": self.obj.id if self.obj else None,
            "this": self.obj,
            "today": self.globals.today,
            "fake": self.faker_template_library,
            "fake_i18n": lambda locale: FakerTemplateLibrary(locale),
            **self.options,
            **self.globals.object_names,
            **self.field_values,
            **self.plugin_function_libraries,
        }

    def field_funcs(self):
        def curry(func):
            rc = partial(func, self)
            if hasattr(func, "lazy"):
                rc.lazy = func.lazy
            return rc

        funcs = {name: curry(func) for name, func in template_funcs.items()}
        return {**funcs}

    def executable_blocks(self):
        return {**self.field_funcs(), "fake": self.fake}

    def fake(self, name):
        return str(getattr(self.faker_template_library, name))

    def get_evaluator(self, definition: str):
        return self.template_evaluator_factory.get_evaluator(definition)


class DynamicEvaluator:
    def __init__(self, template):
        self.template = template

    def __call__(self, context):
        return self.template.render(**context.field_vars(), **context.field_funcs())


def evaluate_function(func, args: Sequence, kwargs: Mapping, context):
    if not hasattr(func, "lazy"):
        args = [arg.render(context) if hasattr(arg, "render") else arg for arg in args]
        kwargs = {
            name: arg.render(context) if hasattr(arg, "render") else arg
            for name, arg in kwargs.items()
        }
    value = func(*args, **kwargs)
    return value


class ObjectRow(yaml.YAMLObject):
    """Represents a single row

    Uses __getattr__ so that the template evaluator can use dot-notation."""

    yaml_loader = yaml.SafeLoader
    yaml_dumper = yaml.SafeDumper
    yaml_tag = "!snowfakery_objectrow"

    __slots__ = ["_tablename", "_values"]

    def __init__(self, tablename, values=()):
        self._tablename = tablename
        self._values = values

    def __getattr__(self, name):
        try:
            return self._values[name]
        except KeyError:
            raise AttributeError(name)

    def __str__(self):
        return str(self.id)

    def __repr__(self):
        return f"<ObjectRow {self._tablename} {self.id}>"

    def __getstate__(self):
        return {"_tablename": self._tablename, "_values": self._values}

    def __setstate__(self, state):
        for slot, value in state.items():
            setattr(self, slot, value)

    @property
    def _name(self):
        return self._values.get("name")


def output_batches(
    output_stream,
    factories: List,
    options: Dict,
    stopping_criteria: Optional[StoppingCriteria] = None,
    continuation_data: Globals = None,
    tables=List[str],
    snowfakery_plugins=Mapping[str, snowfakery.SnowfakeryPlugin],
    faker_providers=List[object],
) -> Globals:
    """Generate 'count' batches to 'output_stream' """
    # check the stopping_criteria against the factories available
    if stopping_criteria:
        stop_table_name = stopping_criteria.tablename
        if stop_table_name not in tables:
            raise DataGenNameError(
                f"No template creating {stop_table_name}", None, None
            )

    if continuation_data:
        globals = continuation_data
        start_ids = {
            name: val + 1 for name, val in globals.id_manager.last_used_ids.items()
        }
    else:
        globals = Globals()
        # at one point start-ids were passed from the command line
        # but for simplicity this feature has been removed and they can only
        # be inferred from the continuation_file.
        start_ids = {}

    runtimecontext = RuntimeContext(
        globaldata=globals,
        current_table_name=None,
        output_stream=output_stream,
        options=options,
        start_ids=start_ids,
        stopping_criteria=stopping_criteria,
        faker_template_library=FakerTemplateLibrary(faker_providers),
        snowfakery_plugins=snowfakery_plugins,
    )
    continuing = bool(continuation_data)
    loop_over_factories(factories, runtimecontext, output_stream, continuing)
    return runtimecontext.globals


def loop_over_factories(factories, runtimecontext, output_stream, continuing):
    finished = False
    while not finished:
        for factory in factories:
            should_skip = factory.just_once and continuing is True
            if not should_skip:
                factory.generate_rows(output_stream, runtimecontext)
        finished = runtimecontext.finished()

        continuing = True
