"""Runtime objects and algorithms used during the generation of rows."""
import os
from collections import defaultdict, ChainMap
from datetime import date, datetime, timezone
from contextlib import contextmanager

from typing import Optional, Dict, Sequence, Mapping, NamedTuple, Set
import typing as T
from warnings import warn

import jinja2
from jinja2 import nativetypes
import yaml

from .utils.template_utils import FakerTemplateLibrary
from .utils.yaml_utils import SnowfakeryDumper, hydrate
from .row_history import RowHistory
from .template_funcs import StandardFuncs
from .data_gen_exceptions import DataGenSyntaxError, DataGenNameError
import snowfakery  # noQA
from snowfakery.object_rows import (
    NicknameSlot,
    SlotState,
    ObjectRow,
    ObjectReference,
    RowHistoryCV,
)
from snowfakery.plugins import PluginContext, SnowfakeryPlugin, ScalarTypes
from snowfakery.utils.collections import OrderedSet

OutputStream = "snowfakery.output_streams.OutputStream"
VariableDefinition = "snowfakery.data_generator_runtime_object_model.VariableDefinition"
ObjectTemplate = "snowfakery.data_generator_runtime_object_model.ObjectTemplate"
Statement = "snowfakery.data_generator_runtime_object_model.Statement"
ParseResult = "snowfakery.parse_recipe_yaml.ParseResult"


# save every single object to history. Useful for testing saving of datatypes
SAVE_EVERYTHING = os.environ.get("SF_SAVE_EVERYTHING")


class StoppingCriteria(NamedTuple):
    """When have we iterated over the Snowfakery script enough times?"""

    tablename: str
    count: int


class IdManager:
    """Keep track of the most recent ID per Object type"""

    def __init__(self):
        self.last_used_ids = defaultdict(lambda: 0)
        self.start_ids = {}

    def generate_id(self, table_name: str) -> int:
        self.last_used_ids[table_name] += 1
        return self.last_used_ids[table_name]

    def __getitem__(self, table_name: str) -> int:
        return self.last_used_ids[table_name]

    def __getstate__(self):
        return {"last_used_ids": dict(self.last_used_ids)}

    def __setstate__(self, state):
        self.last_used_ids = defaultdict(lambda: 0, state["last_used_ids"])
        self.start_ids = {name: val + 1 for name, val in self.last_used_ids.items()}


SnowfakeryDumper.add_representer(defaultdict, SnowfakeryDumper.represent_dict)


class Dependency(NamedTuple):
    table_name_from: str
    table_name_to: str
    field_name: str


yaml.SafeDumper.add_representer(
    Dependency, lambda representer, obj: representer.represent_list(obj)
)


class Transients:
    def __init__(self, nicknames_and_tables: Mapping[str, str], id_manager: IdManager):
        self.nicknamed_objects = {}
        self.last_seen_obj_by_table = {}
        self.named_slots = {
            name: NicknameSlot(table, id_manager)
            for name, table in nicknames_and_tables.items()
        }

        self.orig_used_ids = id_manager.last_used_ids.copy()

    def first_new_id(self, tablename):
        return self.orig_used_ids.get(tablename, 0) + 1

    def last_id_for_table(self, tablename):
        last_obj = self.last_seen_obj_by_table.get(tablename)
        if last_obj:
            return last_obj.id
        else:
            return self.orig_used_ids.get(tablename)


class Globals:
    """Globally named objects and other aspects of global scope

    This object is designed to be persisted to allow long-running
    Snowfakery executions to stop and restart. Other Interpreter internals
    do not persist. For example, it isn't possible to persist a database
    handle in an output_stream."""

    persistent_nicknames: Dict[str, ObjectRow]  # nicknamed objects
    persistent_objects_by_table: Dict[
        str, ObjectRow
    ]  # objects referencable by table name
    id_manager: IdManager  # keeps track of used ids
    intertable_dependencies: Set[Dependency]  # all intertable dependencies detected
    today: date  # today's date
    nicknames_and_tables: Mapping[str, str]  # what table does each nickname refer to?

    def __init__(
        self,
        today: date = None,
        name_slots: Mapping[str, str] = None,
    ):
        # these lists start empty and are filled.
        # They survive iterations and continuations.
        self.persistent_nicknames = {}
        self.persistent_objects_by_table = {}

        self.id_manager = IdManager()
        self.intertable_dependencies = OrderedSet()
        self.today = today or date.today()
        self.nicknames_and_tables = name_slots or {}

        self.reset_slots()

    def register_object(
        self, obj: ObjectRow, nickname: Optional[str], persistent_object: bool
    ):
        """Register an object for lookup by object type and (optionally) Nickname"""
        if nickname:
            if persistent_object:
                self.persistent_nicknames[nickname] = obj
            else:
                self.transients.nicknamed_objects[nickname] = obj
        if persistent_object:
            self.persistent_objects_by_table[obj._tablename] = obj
        self.transients.last_seen_obj_by_table[obj._tablename] = obj

    @property
    def object_names(self):
        """The globally named objects"""
        # the order is important: later overrides earlier
        # i.e. fulfilled names override "slots"
        return {
            **self.transients.named_slots,  # potential forward or backwards references
            **self.persistent_nicknames,  # long-lived nicknames
            **self.persistent_objects_by_table,  # long-lived objects
            **self.transients.nicknamed_objects,  # local nicknames that have been fulfilled
            **self.transients.last_seen_obj_by_table,  # local tablenames that have been fulfilled
        }

    def generate_id_for_nickname(self, nickname: str):
        slot = self.transients.named_slots.get(nickname)
        if slot and slot.status == SlotState.ALLOCATED:
            return slot.consume_slot()

    def register_intertable_reference(
        self, table_name_from: str, table_name_to: str, fieldname: str
    ):
        self.intertable_dependencies.add(
            Dependency(table_name_from, table_name_to, fieldname)
        )

    def reset_slots(self):
        "At the beginning of every iteration, reset the forward reference slots"
        self.transients = Transients(self.nicknames_and_tables, self.id_manager)

    def check_slots_filled(self):
        not_filled = [
            name
            for name, slot in self.transients.named_slots.items()
            if slot.status == SlotState.ALLOCATED
        ]
        if not_filled:
            plural = "s" if len(not_filled) > 1 else ""
            raise DataGenNameError(
                f"Reference{plural} not fulfilled: {','.join(not_filled)}"
            )

    def first_new_id(self, tablename):
        return self.transients.first_new_id(tablename)

    def __getstate__(self):
        def serialize_dict_of_object_rows(dct):
            return {k: v.__getstate__() for k, v in dct.items()}

        persistent_nicknames = serialize_dict_of_object_rows(self.persistent_nicknames)
        persistent_objects_by_table = serialize_dict_of_object_rows(
            self.persistent_objects_by_table
        )
        intertable_dependencies = [
            dict(v._asdict()) for v in self.intertable_dependencies
        ]  # converts ordered-dict to dict for Python 3.6 and 3.7

        state = {
            "persistent_nicknames": persistent_nicknames,
            "persistent_objects_by_table": persistent_objects_by_table,
            "id_manager": self.id_manager.__getstate__(),
            "today": self.today,
            "nicknames_and_tables": self.nicknames_and_tables,
            "intertable_dependencies": intertable_dependencies,
        }
        return state

    def __setstate__(self, state):
        def deserialize_dict_of_object_rows(dct):
            return {k: hydrate(ObjectRow, v) for k, v in dct.items()}

        self.nicknamed_objects = deserialize_dict_of_object_rows(
            state.get("nicknamed_objects", {})
        )
        self.persistent_nicknames = deserialize_dict_of_object_rows(
            state.get("persistent_nicknames", {})
        )
        self.nicknames_and_tables = state["nicknames_and_tables"]
        self.id_manager = hydrate(IdManager, state["id_manager"])

        self.intertable_dependencies = OrderedSet(
            Dependency(*dep) for dep in getattr(state, "intertable_dependencies", [])
        )

        self.today = state["today"]
        persistent_objects_by_table = state.get("persistent_objects_by_table")
        self.persistent_objects_by_table = (
            deserialize_dict_of_object_rows(persistent_objects_by_table)
            if persistent_objects_by_table
            else {}
        )
        self.reset_slots()


class JinjaTemplateEvaluatorFactory:
    def __init__(self, native_types: bool):
        if native_types:
            self.compilers = [
                nativetypes.NativeEnvironment(
                    block_start_string="${%",
                    block_end_string="%}",
                    variable_start_string="${{",
                    variable_end_string="}}",
                )
            ]

            return

        # TODO: Delete this old code_path when the
        #       transition to native_types is complete.
        self.compilers = [
            jinja2.Environment(
                block_start_string="${%",
                block_end_string="%}",
                variable_start_string="${{",
                variable_end_string="}}",
            ),
            jinja2.Environment(
                block_start_string="<%",
                block_end_string="%>",
                variable_start_string="<<",
                variable_end_string=">>",
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
                raise DataGenSyntaxError(str(e)) from e
        else:
            return lambda context: definition


class Interpreter:
    """Snowfakery runtime interpreter state."""

    current_context: "RuntimeContext" = None
    iteration_count = 0

    def __init__(
        self,
        output_stream: OutputStream,
        parse_result: ParseResult,
        globals: Globals,
        *,
        parent_application,
        options: Mapping = None,
        snowfakery_plugins: Optional[Mapping[str, callable]] = None,
        faker_providers: Sequence[object] = (),
        continuing=False,
    ):
        self.output_stream = output_stream
        self.options = options or {}
        self.faker_providers = faker_providers
        snowfakery_plugins = snowfakery_plugins or {}
        self.plugin_instances = {
            name: plugin(self) for name, plugin in snowfakery_plugins.items()
        }
        self.plugin_function_libraries = {
            name: plugin.custom_functions()
            for name, plugin in self.plugin_instances.items()
        }
        self.globals = globals
        self.continuing = continuing
        stop_table_name = parent_application.stopping_tablename
        if stop_table_name and stop_table_name not in parse_result.tables:
            raise DataGenNameError(
                f"No template creating {stop_table_name}",
            )

        # make a plugin context for our Faker stuff to act like a plugin
        self.faker_plugin_context = PluginContext(SnowfakeryPlugin(self))

        self.faker_template_libraries = {}

        # inject context into the standard functions
        standard_funcs_obj = StandardFuncs(self).custom_functions()
        self.standard_funcs = {
            name: getattr(standard_funcs_obj, name)
            for name in dir(standard_funcs_obj)
            if not name.startswith("_") and name != "context"
        }

        self.statements = parse_result.statements
        self.parent_application = parent_application
        self.instance_states = {}
        self.filter_row_values = self.filter_row_values_normal
        snowfakery_version = self.options.get(
            "snowfakery.standard_plugins.SnowfakeryVersion.snowfakery_version", 2
        )
        assert snowfakery_version in (2, 3)
        self.native_types = snowfakery_version == 3
        self.template_evaluator_factory = JinjaTemplateEvaluatorFactory(
            self.native_types
        )
        self.tables_to_keep_history_for = find_tables_to_keep_history_for(
            parse_result, globals.nicknames_and_tables
        )
        self.row_history = RowHistory(
            globals.transients.orig_used_ids,
            self.tables_to_keep_history_for,
            self.globals.nicknames_and_tables,
        )
        self.resave_objects_from_continuation(globals, self.tables_to_keep_history_for)

    def resave_objects_from_continuation(
        self, globals: Globals, tables_to_keep_history_for: T.Iterable[str]
    ):
        """Re-save just_once objects to the local history cache after resuming a continuation"""

        # deal with objs known by their nicknames
        relevant_objs = [
            (obj._tablename, nickname, obj)
            for nickname, obj in globals.persistent_nicknames.items()
        ]
        already_saved = set(obj._id for (_, _, obj) in relevant_objs)
        # and those known by their tablename, if not already in the list
        relevant_objs.extend(
            (tablename, None, obj)
            for tablename, obj in globals.persistent_objects_by_table.items()
            if obj._id not in already_saved
        )
        # filter out those in tables that are not history-backed
        relevant_objs = (
            (table, nick, obj)
            for (table, nick, obj) in relevant_objs
            if table in tables_to_keep_history_for
        )
        for tablename, nickname, obj in relevant_objs:
            self.row_history.save_row(tablename, nickname, obj._values)

    def execute(self):
        RowHistoryCV.set(self.row_history)
        self.current_context = RuntimeContext(interpreter=self)
        self.loop_over_templates_until_finished(self.continuing)
        return self.globals

    def faker_template_library(self, locale):
        """Create a faker template library for locale, or retrieve it from a cache"""
        rc = self.faker_template_libraries.get(locale)
        if not rc:
            rc = FakerTemplateLibrary(
                self.faker_providers,
                locale,
                self.faker_plugin_context,
            )
            self.faker_template_libraries[locale] = rc
        return rc

    def loop_over_templates_until_finished(self, continuing):
        finished = False
        self.current_context = RuntimeContext(interpreter=self)
        while not finished:
            self.loop_over_templates_once(self.statements, continuing)
            finished = self.current_context.check_if_finished()
            self.iteration_count += 1
            continuing = True
            self.globals.reset_slots()
            self.row_history.reset_locals()

    def loop_over_templates_once(self, statement_list, continuing: bool):
        for statement in statement_list:
            statement.execute(self, self.current_context, continuing)

    def register_variable(self, name: str, value: object):
        vardefs = self.current_context.variable_definitions()
        vardefs[name] = value

    def __enter__(self, *args):
        return self

    def __exit__(self, *args):
        for plugin in self.plugin_instances.values():
            try:
                plugin.close()
            except Exception as e:
                warn(f"Could not close {plugin} because {e}")

    def get_contextual_state(
        self,
        *,
        make_state_func: T.Callable,
        name: T.Union[str, tuple, None] = None,
        parent: T.Optional[str] = None,
        reset_every_iteration: bool = False,
    ):
        """Get state that is specific to a particular template&plugin

        The first time the template is invoked in a particular context,
        make_state_func is invoked to generate the state container.

        The next time it is invoked, the state will be returned for reuse
        and potential modification.

        `name` allows you to reuse the same state among multiple templates.
        The function should generally expose this to the end-user
        through an argument called `name`.

        `parent` allows the user to use some specific Object parent as
        a parent object. The state will be only reused for the lifetime
        of the parent and then discarded. This should also be
        user-controlled.

        `reset_every_iteration` is an experimental feature that should
        not generally be used.
        """
        assert not reset_every_iteration
        current_context = self.current_context
        uniq_name = name or current_context.unique_context_identifier
        if parent:
            parent_obj = current_context.field_vars().get(parent)
        # elif reset_every_iteration:           # in case we bring back this feature
        #     parent_obj = self.iteration_count
        else:
            parent_obj = None
        current_parent, value = self.instance_states.get(uniq_name, (None, None))
        if current_parent != parent_obj or value is None:
            value = make_state_func()
            self.instance_states[uniq_name] = [parent_obj, value]
        return value

    def filter_row_values_normal(self, row: dict):
        return {k: v for k, v in row.items() if not k.startswith("__")}

    # for future use:

    # def filter_row_values_and_remove_ids(self, row: dict):
    #     return {k: v for k, v in row.items() if not k.startswith("__") or k == "id"}


class RuntimeContext:
    """Local "stack frame" type object. RuntimeContexts live on the Python stack.

    There are many proxy methods for other objects which helps keep the
    internals of the runtime hidden from outside code to make maintenance
    easier. From the point of view of other modules this is "the interpreter"
    but internally its mostly just proxying to other classes."""

    obj: Optional[ObjectRow] = None
    current_template = None
    local_vars = None
    unique_context_identifier = None
    recalculate_every_time = False  # by default, data is recalculated constantly

    def __init__(
        self,
        interpreter: Interpreter,
        current_template: Statement = None,
        parent_context: "RuntimeContext" = None,
    ):
        if current_template:
            self.current_table_name = current_template.tablename
            self.current_template = current_template

        self.interpreter = interpreter
        self.parent = parent_context
        if self.parent:
            self._plugin_context_vars = self.parent._plugin_context_vars.new_child()
            # are we in a re-calculate everything context?
            self.recalculate_every_time = parent_context.recalculate_every_time
        else:
            self._plugin_context_vars = ChainMap()
        locale = self.variable_definitions().get("snowfakery_locale")
        self.faker_template_library = self.interpreter.faker_template_library(locale)
        self.local_vars = {}

    @property
    def filter_row_values(self):
        return self.interpreter.filter_row_values

    # TODO: move this into the interpreter object
    def check_if_finished(self):
        "Have we iterated over the script enough times?"
        # check that every forward reference was resolved
        globls = self.interpreter.globals
        app = self.interpreter.parent_application

        globls.check_slots_filled()
        app.ensure_progress_was_made(globls.id_manager)

        return app.check_if_finished(globls.id_manager)

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
        # otherwise just create a new one
        rc = rc or self.interpreter.globals.id_manager.generate_id(
            self.current_table_name
        )
        return rc

    def remember_row(self, tablename: str, nickname: T.Optional[str], row: dict):
        for fieldname, fieldvalue in row.items():
            if isinstance(fieldvalue, (ObjectRow, ObjectReference)):
                self.interpreter.globals.register_intertable_reference(
                    tablename, fieldvalue._tablename, fieldname
                )
        history_tables = self.interpreter.tables_to_keep_history_for
        should_save: bool = (
            (tablename in history_tables)
            or (nickname in history_tables)
            or SAVE_EVERYTHING
        )
        if should_save:
            self.interpreter.row_history.save_row(tablename, nickname, row)

    def register_object(self, obj, name: Optional[str], persistent: bool):
        "Keep track of this object in case other objects refer to it."
        self.obj = obj
        self.interpreter.globals.register_object(obj, name, persistent)

    @contextmanager
    def child_context(self, template):
        "Create a nested RuntimeContext (analogous to a 'stack frame')."
        jr = self.__class__(
            current_template=template,
            interpreter=self.interpreter,
            parent_context=self,
        )
        try:
            self.interpreter.current_context = jr
            yield jr
        finally:
            # Goodbye junior, its been nice
            # Hope you find your paradise
            self.interpreter.current_context = self

    @property
    def output_stream(self):
        return self.interpreter.output_stream

    def get_evaluator(self, definition: str):
        return self.interpreter.template_evaluator_factory.get_evaluator(definition)

    @property
    def evaluation_namespace(self):
        return EvaluationNamespace(self)

    def executable_blocks(self):
        return self.evaluation_namespace.executable_blocks()

    def field_vars(self):
        return self.evaluation_namespace.field_vars()

    def context_vars(self, plugin_namespace):
        """Variables which are inherited by child scopes"""
        # This looks like a candidate for optimization.
        # An unconditional object copy seems expensive.
        local_plugin_vars = self._plugin_context_vars.get(plugin_namespace, {}).copy()
        self._plugin_context_vars[plugin_namespace] = local_plugin_vars
        return local_plugin_vars

    def variable_definitions(self):
        return self.context_vars("variable definitions")


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
            "now": datetime.now(timezone.utc),
            "fake": self.runtime_context.faker_template_library,
            "template": self.runtime_context.current_template,
            **interpreter.options,
            **interpreter.globals.object_names,
            **(obj._values if obj else {}),
            **interpreter.plugin_function_libraries,
            **self.runtime_context.variable_definitions(),
        }

    def field_funcs(self):
        "Injects context into functions from template_funcs module."

        return self.runtime_context.interpreter.standard_funcs

    def executable_blocks(self):
        "Return mapping of functions that can be used in YAML block functions"
        return {**self.field_funcs(), "fake": self.fake}

    def fake(self, name):
        val = self.runtime_context.faker_template_library._get_fake_data(name)
        if isinstance(val, ScalarTypes):
            return val
        else:
            return str(val)

    def field_vars(self):
        return {**self.simple_field_vars(), **self.field_funcs()}


def evaluate_function(func, args: Sequence, kwargs: Mapping, context):
    if not hasattr(func, "lazy"):
        args = [arg.render(context) if hasattr(arg, "render") else arg for arg in args]
        kwargs = {
            name: arg.render(context) if hasattr(arg, "render") else arg
            for name, arg in kwargs.items()
        }
    return func(*args, **kwargs)


def find_tables_to_keep_history_for(
    parse_result: ParseResult, nicknames_and_tables: T.Dict[str, str]
) -> T.Set[str]:
    """Only keep history for certain tables that are actually referred to by random_reference"""
    random_references = parse_result.random_references
    referenced_names = set(
        get_referent_name(random_reference) for random_reference in random_references
    )
    # normalize nicknames to their underlying table
    referenced_tables = set(
        nicknames_and_tables.get(name, name) for name in referenced_names
    )
    return referenced_tables


def get_referent_name(random_reference):
    """What does this random_reference refer to?"""
    args, kwargs = random_reference.args, random_reference.kwargs
    assert not (args and kwargs)
    if args:
        ret = args[0].definition
    elif kwargs:
        ret = kwargs["to"].definition
    if not isinstance(ret, str):
        raise DataGenSyntaxError(
            f"random_reference should only refer to a name, not {ret}"
        )
    return ret
