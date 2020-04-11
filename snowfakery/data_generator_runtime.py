from collections import defaultdict
from functools import partial
from datetime import date
from contextlib import contextmanager

from typing import Optional, Dict, List, Sequence, Mapping, NamedTuple

from faker.utils.datetime_safe import date as faker_date
import jinja2
import yaml

from .utils.template_utils import FakerTemplateLibrary

from .template_funcs import template_funcs
from .data_gen_exceptions import DataGenSyntaxError, DataGenNameError
import snowfakery  # noqa

OutputStream = "snowfakery.output_streams.OutputStream"


# Runtime objects and algorithms used during the generation of rows.


class StoppingCriteria(NamedTuple):
    """When have we iterated over the Snowfakery script enough times?"""

    tablename: str
    count: int


class FinishedChecker:
    """Checks whether the Stopping Criteria have been met"""

    stopping_criteria: StoppingCriteria

    def __init__(self, start_ids, stopping_criteria):
        self.start_ids = start_ids
        self.stopping_criteria = stopping_criteria
        self.target_progress_id = 0

    def check_if_finished(self, id_manager):
        "Check whether we've finished making as many objects as we promised"
        # if nobody told us how much to make, finish after first run
        if not self.stopping_criteria:
            return True

        target_table, count = self.stopping_criteria

        # Snowfakery processes can be restarted. We would need
        # to keep track of where we restarted to know whether
        # we are truly finished
        if self.start_ids:
            start = self.start_ids.get(target_table, 1)
        else:
            start = 1
        target_id = start + count - 1

        last_used_id = id_manager[target_table]

        self.ensure_progress_was_made(last_used_id, target_id)

        return last_used_id >= target_id

    def ensure_progress_was_made(self, last_used_id, target_id):
        """Check that we are actually making progress towards our goal"""
        if last_used_id == self.target_progress_id:
            raise RuntimeError(
                f"{self.stopping_criteria.tablename} max ID was {self.target_progress_id} "
                f"before evaluating factory and is {last_used_id} after. "
                f"At this rate we will never hit our target of {target_id}!"
            )

        self.target_progress_id = last_used_id


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


yaml.SafeDumper.add_representer(
    faker_date, yaml.representer.SafeRepresenter.represent_date
)


class Globals(yaml.YAMLObject):
    """Globally named objects and other aspects of global scope

     This object is designed to be persisted to allow long-running
     Snowfakery executions to stop and restart. Other Interpreter internals
     do not persist. For example, it isn't possible to persist a database
     handle in an output_stream."""

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
                return lambda context: template.render(context.field_vars())
            except jinja2.exceptions.TemplateSyntaxError as e:
                raise DataGenSyntaxError(str(e), None, None) from e
        else:
            return lambda context: definition


class Interpreter:
    """Snowfakery runtime interpreter state."""

    current_context: "RuntimeContext" = None

    def __init__(
        self,
        output_stream: OutputStream,
        globals: Globals = None,
        options: Mapping = None,
        snowfakery_plugins: Optional[Mapping[str, callable]] = None,
        stopping_criteria: Optional[StoppingCriteria] = None,
        start_ids: Optional[Mapping[str, int]] = None,
        faker_providers: Sequence[object] = (),
    ):
        self.output_stream = output_stream
        self.options = options or {}
        snowfakery_plugins = snowfakery_plugins or {}
        # todo: some caching of these could speed things up a bit
        self.plugin_function_libraries = {
            name: plugin(self).custom_functions()
            for name, plugin in snowfakery_plugins.items()
        }
        self.finished_checker = FinishedChecker(start_ids, stopping_criteria)
        self.faker_template_library = FakerTemplateLibrary(faker_providers)
        self.globals = globals or Globals()


class RuntimeContext:
    """Local "stack frame" type object. RuntimeContexts live on the Python stack.

    There are many proxy methods for other objects which helps keep the
    internals of the runtime hidden from outside code to make maintenance
    easier. From the point of view of other modules this is "the interpreter"
    but internally its mostly just proxying to other classes."""

    obj: Optional["ObjectRow"] = None
    template_evaluator_factory = JinjaTemplateEvaluatorFactory()

    def __init__(
        self,
        interpreter: Interpreter,
        current_table_name: Optional[str] = None,
        parent_context: "RuntimeContext" = None,
    ):
        self.current_table_name = current_table_name
        self.interpreter = interpreter
        self.interpreter.current_context = self
        self.parent = parent_context
        if self.parent:
            self._context_vars = {
                **self.parent._context_vars
            }  # implements variable inheritance
        else:
            self._context_vars = {}

    def check_if_finished(self):
        "Have we iterated over the script enough times?"
        return self.interpreter.finished_checker.check_if_finished(
            self.interpreter.globals.id_manager
        )

    def generate_id(self):
        "Generate a unique ID for this object"
        return self.interpreter.globals.id_manager.generate_id(self.current_table_name)

    def register_object(self, obj, name=None):
        "Keep track of this object in case its children refer to it."
        self.obj = obj
        self.interpreter.globals.register_object(obj, name)

    def register_intertable_reference(self, table_name_from, table_name_to, fieldname):
        "Keep track of a dependency between two tables. e.g. for mapping file generation"
        self.interpreter.globals.register_intertable_reference(
            table_name_from, table_name_to, fieldname
        )

    @contextmanager
    def child_context(self, tablename):
        "Create a nested RuntimeContext (analogous to a 'stack frame')."
        jr = self.__class__(
            current_table_name=tablename,
            interpreter=self.interpreter,
            parent_context=self,
        )
        # jr will register itself with the interpreter
        try:
            yield jr
        finally:
            # Goodbye junior, its been nice
            # Hope you find your paradise
            self.interpreter.current_context = self

    @property
    def output_stream(self):
        return self.interpreter.output_stream

    def get_evaluator(self, definition: str):
        return self.template_evaluator_factory.get_evaluator(definition)

    @property
    def evaluation_namespace(self):
        return EvaluationNamespace(self)

    def executable_blocks(self):
        return self.evaluation_namespace.executable_blocks()

    def field_vars(self):
        return self.evaluation_namespace.field_vars()

    def context_vars(self, plugin_namespace):
        return self._context_vars.setdefault(plugin_namespace, {})


# NamedTuple because it is immutable, efficient and auto-generates init
class EvaluationNamespace(NamedTuple):
    """Supplies names for evaluation of YAML trees and Jinja expressions."""

    runtime_context: RuntimeContext

    def simple_field_vars(self):
        "Variables that can be inserted into templates"
        # obj=None in some contexts, e.g. evaluating count
        obj = self.runtime_context.obj
        interpreter = self.runtime_context.interpreter
        return {
            "id": obj.id if obj else None,
            "count": obj.id if obj else None,
            "this": obj,
            "today": interpreter.globals.today,
            "fake": interpreter.faker_template_library,
            "fake_i18n": lambda locale: FakerTemplateLibrary(locale),
            **interpreter.options,
            **interpreter.globals.object_names,
            **(obj._values if obj else {}),
            **interpreter.plugin_function_libraries,
        }

    # todo: should be replaced with the plugin architecture
    def field_funcs(self):
        "Injects context into functions from template_funcs module."

        def curry(func):
            rc = partial(func, self.runtime_context)
            if hasattr(func, "lazy"):
                rc.lazy = func.lazy
            return rc

        funcs = {name: curry(func) for name, func in template_funcs.items()}
        return {**funcs}

    def executable_blocks(self):
        "Return mapping of functions that can be used in YAML block functions"
        return {**self.field_funcs(), "fake": self.fake}

    # todo: remove this special case
    def fake(self, name):
        return str(
            getattr(self.runtime_context.interpreter.faker_template_library, name)
        )

    def field_vars(self):
        return {**self.simple_field_vars(), **self.field_funcs()}


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
    tables: Mapping[str, int] = None,
    snowfakery_plugins: Mapping[str, snowfakery.SnowfakeryPlugin] = None,
    faker_providers: List[object] = None,
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

    interpreter = Interpreter(
        output_stream=output_stream,
        globals=globals,
        options=options,
        snowfakery_plugins=snowfakery_plugins,
        stopping_criteria=stopping_criteria,
        start_ids=start_ids,
        faker_providers=faker_providers,
    )

    runtimecontext = RuntimeContext(interpreter=interpreter)
    continuing = bool(continuation_data)
    loop_over_factories(factories, runtimecontext, output_stream, continuing)
    return interpreter.globals


def loop_over_factories(factories, runtimecontext, output_stream, continuing):
    finished = False
    while not finished:
        for factory in factories:
            should_skip = factory.just_once and continuing is True
            if not should_skip:
                factory.generate_rows(output_stream, runtimecontext)
        finished = runtimecontext.check_if_finished()

        continuing = True
