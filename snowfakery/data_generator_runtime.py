from collections import defaultdict
from datetime import date
from contextlib import contextmanager
from enum import Enum, auto

from typing import Optional, Dict, List, Sequence, Mapping, NamedTuple

import jinja2
import yaml

from .utils.template_utils import FakerTemplateLibrary
from .utils.yaml_utils import SnowfakeryDumper, hydrate

from .template_funcs import StandardFuncs
from .data_gen_exceptions import DataGenSyntaxError, DataGenNameError
import snowfakery

OutputStream = "snowfakery.output_streams.OutputStream"
ObjectTemplate = "snowfakery.data_generator_runtime_object_model.ObjectTemplate"

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
                f"before evaluating recipe and is {last_used_id} after. "
                f"At this rate we will never hit our target of {target_id}!"
            )

        self.target_progress_id = last_used_id


class IdManager:
    """Keep track of the most recent ID per Object type"""

    def __init__(self, start_ids: Optional[Dict[str, int]] = None):
        start_ids = start_ids or {}
        self.last_used_ids = defaultdict(lambda: 0)

    def generate_id(self, table_name: str) -> int:
        self.last_used_ids[table_name] += 1
        return self.last_used_ids[table_name]

    def __getitem__(self, table_name: str) -> int:
        return self.last_used_ids[table_name]

    def __getstate__(self):
        return {"last_used_ids": dict(self.last_used_ids)}

    def __setstate__(self, state):
        self.last_used_ids = defaultdict(lambda: 0, state["last_used_ids"])


SnowfakeryDumper.add_representer(defaultdict, SnowfakeryDumper.represent_dict)


class Dependency(NamedTuple):
    table_name_from: str
    table_name_to: str
    field_name: str


yaml.SafeDumper.add_representer(
    Dependency, lambda representer, obj: representer.represent_list(obj)
)


class SlotState(Enum):
    """The current state of a NicknameSlot.

    UNUSED=empty, ALLOCATED=referenced, CONSUMED=object generated"""

    UNUSED = auto()
    ALLOCATED = auto()
    CONSUMED = auto()


class NicknameSlot:
    """A slot that represents a Nickname or Tablename"""

    _tablename: str
    id_manager: IdManager
    allocated_id: int = None

    def __init__(self, tablename, id_manager):
        self._tablename = tablename
        self.id_manager = id_manager

    @property
    def id(self):
        "Get an id corresponding to this slot. Generate one if necessary."
        if self.allocated_id is None:
            self.allocated_id = self.id_manager.generate_id(self._tablename)
        return self.allocated_id

    def consume_slot(self):
        "Mark a slot as filled by an object and return its id for use by the object."
        rc = self.allocated_id
        self.allocated_id = SlotState.CONSUMED
        return rc

    @property
    def status(self):
        "Is the slot empty/unreferenced, allocated/referenced or consumed/used"
        if self.allocated_id is None:
            return SlotState.UNUSED
        elif isinstance(self.allocated_id, int):
            return SlotState.ALLOCATED
        elif self.allocated_id == SlotState.CONSUMED:
            return SlotState.CONSUMED

    def __repr__(self):
        return f"<NicknameSlot {vars(self)}>"


class Globals:
    """Globally named objects and other aspects of global scope

    This object is designed to be persisted to allow long-running
    Snowfakery executions to stop and restart. Other Interpreter internals
    do not persist. For example, it isn't possible to persist a database
    handle in an output_stream."""

    def __init__(
        self,
        today: date = None,
        name_slots: Mapping[str, str] = None,
    ):
        # list starts empty and is filled. Survives continuations.
        self.nicknamed_objects = {}

        self.id_manager = IdManager()
        self.last_seen_obj_of_type = {}
        self.intertable_dependencies = set()
        self.today = today or date.today()
        self.nicknames_and_tables = name_slots or {}
        self.reset_slots()

    def register_object(self, obj, nickname: str = None):
        """Register an object for lookup by object type and (optionally) Nickname"""
        if nickname:
            self.nicknamed_objects[nickname] = obj
        self.last_seen_obj_of_type[obj._tablename] = obj

    @property
    def object_names(self):
        """The globally named objects"""
        # the order is important: later overrides earlie
        return {
            **self.named_slots,  # potential forward or backwards references
            **self.nicknamed_objects,  # nicknames that have been fulfilled
            **self.last_seen_obj_of_type,  # tablenames that have been fulfilled
        }

    def generate_id_for_nickname(self, nickname: str):
        slot = self.named_slots.get(nickname)
        if slot and slot.status == SlotState.ALLOCATED:
            return slot.consume_slot()

    def register_intertable_reference(
        self, table_name_from: str, table_name_to: str, fieldname: str
    ):
        self.intertable_dependencies.add(
            Dependency(table_name_from, table_name_to, fieldname)
        )

    def reset_slots(self, nicknamed_objects: Dict = None):
        "At the beginning of every execution, reset the forward reference slots"
        self.named_slots = {
            name: NicknameSlot(table, self.id_manager)
            for name, table in self.nicknames_and_tables.items()
        }
        if nicknamed_objects:
            nicknames_with_slots = set(nicknamed_objects.keys()).intersection(
                self.named_slots.keys()
            )
            for name in nicknames_with_slots:
                self.named_slots[name].consume_slot()

    def check_slots_filled(self):
        not_filled = [
            name
            for name, slot in self.named_slots.items()
            if slot.status == SlotState.ALLOCATED
        ]
        if not_filled:
            plural = "s" if len(not_filled) > 1 else ""
            raise DataGenNameError(
                f"Reference{plural} not fulfilled: {','.join(not_filled)}",
                None,
                None,
            )

    def __getstate__(self):
        id_manager = self.id_manager
        nicknamed_objects = {
            k: v.__getstate__() for k, v in self.nicknamed_objects.items()
        }
        nicknames_and_tables = {k: v for k, v in self.nicknames_and_tables.items()}
        today = self.today
        intertable_dependencies = [
            dict(v._asdict()) for v in self.intertable_dependencies
        ]  # converts ordered-dict to dict for Python 3.6 and 3.7
        return {
            "id_manager": id_manager.__getstate__(),
            "nicknamed_objects": nicknamed_objects,
            "nicknames_and_tables": nicknames_and_tables,
            "today": today,
            "intertable_dependencies": intertable_dependencies,
        }

    def __setstate__(self, dct):
        self.id_manager = hydrate(IdManager, dct["id_manager"])
        self.last_seen_obj_of_type = {}
        self.nicknamed_objects = {
            k: hydrate(ObjectRow, v)
            for k, v in dct.get("nicknamed_objects", {}).items()
        }
        self.nicknames_and_tables = dct["nicknames_and_tables"]
        self.today = dct["today"]
        self.intertable_dependencies = set(
            Dependency(**x) for x in dct.get("intertable_dependencies", ())
        )
        self.reset_slots(self.nicknamed_objects)


class JinjaTemplateEvaluatorFactory:
    def __init__(self):
        self.compilers = [
            jinja2.Environment(
                block_start_string="<%",
                block_end_string="%>",
                variable_start_string="<<",
                variable_end_string=">>",
            ),
            jinja2.Environment(
                block_start_string="${%",
                block_end_string="%}",
                variable_start_string="${{",
                variable_end_string="}}",
            ),
        ]

    def compiler_for_string(self, definition: str):
        for compiler in self.compilers:
            for delimiter in ["block_start_string", "variable_start_string"]:
                if getattr(compiler, delimiter) in definition:
                    return compiler
        return None

    def get_evaluator(self, definition: str):
        assert isinstance(definition, str), definition
        compiler = self.compiler_for_string(definition)

        if compiler:
            try:
                template = compiler.from_string(definition)
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
        templates: Sequence[ObjectTemplate] = (),
    ):
        self.output_stream = output_stream
        self.options = options or {}
        snowfakery_plugins = snowfakery_plugins or {}
        self.plugin_instances = {
            name: plugin(self) for name, plugin in snowfakery_plugins.items()
        }
        self.plugin_function_libraries = {
            name: plugin.custom_functions()
            for name, plugin in self.plugin_instances.items()
        }
        self.finished_checker = FinishedChecker(start_ids, stopping_criteria)
        self.faker_template_library = FakerTemplateLibrary(faker_providers)

        # TODO: clean this duplicated code up
        name_slots = {
            template.nickname: template.tablename
            for template in templates
            if template.nickname
        }

        # table names are sort of nicknames for themselves too, because
        # you can refer to them.
        name_slots.update(
            {template.tablename: template.tablename for template in templates}
        )
        # print("XXXX", name_slots, globals)

        self.globals = globals or Globals(name_slots=name_slots)

        # inject context into the standard functions
        standard_funcs_obj = StandardFuncs(self).custom_functions()
        self.standard_funcs = {
            name: getattr(standard_funcs_obj, name)
            for name in dir(standard_funcs_obj)
            if not name.startswith("_") and name != "context"
        }

        self.templates = templates

    def loop_over_templates_until_finished(self, runtimecontext, continuing):
        finished = False
        while not finished:
            self.loop_over_templates_once(runtimecontext, continuing)
            finished = runtimecontext.check_if_finished()
            continuing = True

    def loop_over_templates_once(self, runtimecontext, continuing):
        for template in self.templates:
            should_skip = template.just_once and continuing
            if not should_skip:
                template.generate_rows(self.output_stream, runtimecontext)

    def __enter__(self, *args):
        return self

    def __exit__(self, *args):
        for plugin in self.plugin_instances.values():
            plugin.close()


class RuntimeContext:
    """Local "stack frame" type object. RuntimeContexts live on the Python stack.

    There are many proxy methods for other objects which helps keep the
    internals of the runtime hidden from outside code to make maintenance
    easier. From the point of view of other modules this is "the interpreter"
    but internally its mostly just proxying to other classes."""

    obj: Optional["ObjectRow"] = None
    template_evaluator_recipe = JinjaTemplateEvaluatorFactory()
    current_template = None

    def __init__(
        self,
        interpreter: Interpreter,
        current_template: ObjectTemplate = None,
        parent_context: "RuntimeContext" = None,
    ):
        if current_template:
            self.current_table_name = current_template.tablename
            self.current_template = current_template

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
        # check that every forward reference was resolved
        self.interpreter.globals.check_slots_filled()
        return self.interpreter.finished_checker.check_if_finished(
            self.interpreter.globals.id_manager
        )

    def generate_id(self, nickname: Optional[str]):
        "Generate a unique ID for this object"
        rc = None
        # check if an ID has already been assigned based on the nickname
        # (due to a forward reference)
        if nickname:
            rc = self.interpreter.globals.generate_id_for_nickname(nickname)
        # check if an ID has already been assigned based on the tablenmae.
        # (due to a forward reference)
        rc = rc or self.interpreter.globals.generate_id_for_nickname(
            self.current_table_name
        )
        # othewise just create a new one
        rc = rc or self.interpreter.globals.id_manager.generate_id(
            self.current_table_name
        )
        return rc

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
    def child_context(self, template):
        "Create a nested RuntimeContext (analogous to a 'stack frame')."
        jr = self.__class__(
            current_template=template,
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
        return self.template_evaluator_recipe.get_evaluator(definition)

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
            "child_index": obj._child_index if obj else None,
            "this": obj,
            "today": interpreter.globals.today,
            "fake": interpreter.faker_template_library,
            "template": self.runtime_context.current_template,
            **interpreter.options,
            **interpreter.globals.object_names,
            **(obj._values if obj else {}),
            **interpreter.plugin_function_libraries,
        }

    def field_funcs(self):
        "Injects context into functions from template_funcs module."

        return self.runtime_context.interpreter.standard_funcs

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
    yaml_dumper = SnowfakeryDumper
    yaml_tag = "!snowfakery_objectrow"

    __slots__ = ["_tablename", "_values", "_child_index"]

    def __init__(self, tablename, values=(), index=0):
        self._tablename = tablename
        self._values = values
        self._child_index = index

    def __getattr__(self, name):
        try:
            return self._values[name]
        except KeyError:
            raise AttributeError(name)

    def __str__(self):
        return str(self.id)

    def __repr__(self):
        try:
            return f"<ObjectRow {self._tablename} {self.id}>"
        except Exception:
            return super().__repr__()

    def __getstate__(self):
        """Get the state of this ObjectRow for serialization.

        Do not include related ObjectRows because circular
        references in serialization formats cause problems."""
        values = {k: v for k, v in self._values.items() if not isinstance(v, ObjectRow)}
        return {"_tablename": self._tablename, "_values": values}

    def __setstate__(self, state):
        for slot, value in state.items():
            setattr(self, slot, value)

    @property
    def _name(self):
        return self._values.get("name")


def output_batches(
    output_stream,
    templates: List,
    options: Dict,
    stopping_criteria: Optional[StoppingCriteria] = None,
    continuation_data: Globals = None,
    tables: Mapping[str, int] = None,
    snowfakery_plugins: Mapping[str, snowfakery.SnowfakeryPlugin] = None,
    faker_providers: List[object] = None,
) -> Globals:
    """Generate 'count' batches to 'output_stream' """
    # check the stopping_criteria against the templates available
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
        name_slots = {
            template.nickname: template.tablename
            for template in templates
            if template.nickname
        }
        name_slots.update(
            {template.tablename: template.tablename for template in templates}
        )
        # print("YYYY", name_slots)

        globals = Globals(name_slots=name_slots)
        # at one point start-ids were passed from the command line
        # but for simplicity this feature has been removed and they can only
        # be inferred from the continuation_file.
        start_ids = {}

    with Interpreter(
        output_stream=output_stream,
        globals=globals,
        options=options,
        snowfakery_plugins=snowfakery_plugins,
        stopping_criteria=stopping_criteria,
        start_ids=start_ids,
        faker_providers=faker_providers,
        templates=templates,
    ) as interpreter:

        runtimecontext = RuntimeContext(interpreter=interpreter)
        continuing = bool(continuation_data)
        interpreter.loop_over_templates_until_finished(runtimecontext, continuing)
        return interpreter.globals
