from abc import abstractmethod, ABC
from .data_generator_runtime import evaluate_function, RuntimeContext, Interpreter
from .object_rows import ObjectRow, ObjectReference
from contextlib import contextmanager
from typing import NamedTuple, Union, Dict, Sequence, Optional, cast
from .utils.template_utils import look_for_number
import itertools
import jinja2

from .data_gen_exceptions import (
    DataGenError,
    DataGenNameError,
    DataGenSyntaxError,
    DataGenValueError,
    fix_exception,
)
from .plugins import Scalar, PluginResult, PluginResultIterator

# objects that represent the hierarchy of a data generator.
# roughly similar to the YAML structure but with domain-specific objects
Definition = Union["ObjectTemplate", "SimpleValue", "StructuredValue"]
FieldValue = Union[None, Scalar, ObjectRow, tuple, PluginResult, ObjectReference]


class FieldDefinition(ABC):
    """Base class for things that render fields

    Abstract base class for everything that can fulfill the role of X in

    - object: abc
      fields:
         fieldname: X
    """

    @abstractmethod
    def render(self, context: RuntimeContext) -> FieldValue:
        pass

    @contextmanager
    def exception_handling(self, message: str, *args, **kwargs):
        try:
            yield
        except Exception as e:
            raise fix_exception(message, self, e, *args, **kwargs) from e


class VariableDefinition:
    """Defines a mutable variable. Like:

    - var: Foo
      value: Bar
    """

    # TODO: Add an example

    tablename = None

    def __init__(
        self,
        filename: str,
        line_num: int,
        varname: str,
        expression: Definition,
    ):
        self.varname = varname
        self.expression = expression
        self.filename = filename
        self.line_num = line_num

    def evaluate(self, context: RuntimeContext) -> FieldValue:
        """Evaluate the expression"""
        return self.expression.render(context)

    def execute(
        self, interp: Interpreter, parent_context: RuntimeContext, continuing: bool
    ) -> Optional[dict]:
        with parent_context.child_context(self) as context:
            name = self.varname
            value = self.evaluate(context)
        interp.register_variable(name, value)


class ForEachVariableDefinition:
    """Represents a for_each statement."""

    varname: str
    expression: "StructuredValue"

    def __init__(
        self, filename: str, line_num: int, varname: str, expression: Definition
    ):
        self.varname = varname
        self.expression = expression
        self.filename = filename
        self.line_num = line_num

    def evaluate(self, context: RuntimeContext) -> FieldValue:
        """Disable value caching for this context and evaluate the expression"""
        context.recalculate_every_time = True
        ret = self.expression.render(context)
        if not isinstance(ret, PluginResultIterator):
            raise DataGenValueError(
                f"`for_each` value must be a DatasetIterator for `{self.varname}`",
                self.filename,
                self.line_num,
            )
        ret.repeat = False
        return ret


class LoopIterator(NamedTuple):
    name: str
    iterator: object


class ObjectTemplate:
    """A factory that generates rows.

    The runtime equivalent of

    - object: tablename
      count: count_expr   # counts can be dynamic so they are expressions
      fields: list of FieldFactories
      friends: list of other ObjectTemplates
      nickname: string
    """

    def __init__(
        self,
        tablename: str,
        filename: str,
        line_num: int,
        nickname: str = None,
        count_expr: FieldDefinition = None,  # counts can be dynamic so they are expressions
        for_each_expr: ForEachVariableDefinition = None,
        just_once: bool = False,
        fields: Sequence = (),
        friends: Sequence = (),
        update_key: str = None,
    ):
        self.tablename = tablename
        self.nickname = nickname
        self.count_expr = count_expr
        self.just_once = just_once
        self.filename = filename
        self.line_num = line_num
        self.fields = fields
        self.friends = friends
        self.for_each_expr = for_each_expr
        self.update_key = update_key

        if count_expr and for_each_expr:
            raise DataGenSyntaxError(
                f"Cannot specify both a count expression and a for-each expression at the same time in declaration for {self.tablename}.",
                self.filename,
                self.line_num,
            )

    def render(self, context: RuntimeContext) -> Optional[ObjectRow]:
        return self.generate_rows(context.output_stream, context)

    def generate_rows(
        self, output_stream, parent_context: RuntimeContext
    ) -> Optional[ObjectRow]:
        """Generate several rows"""
        rc = None
        with parent_context.child_context(self) as context:
            if self.for_each_expr:
                # it would be easy to support multiple parallel
                # for-eaches here and at one point the code did,
                # but the use-case wasn't obvious so it was removed
                # after 9bc296a7df. If we get to 2023 without
                # # finding a use-case we can delete this comment.
                iterators = [self._evaluate_for_each(context)]
                iterators.append(LoopIterator("child_index", itertools.count()))
            else:  # use a count, or a default count of 1
                iterators = [
                    LoopIterator(
                        "child_index", iter(range(self._evaluate_count(context)))
                    )
                ]
            with self.exception_handling(f"Cannot generate {self.name}"):
                master_iterator = zip(*(it.iterator for it in iterators))
                iterator_names = [it.name for it in iterators]
                for i, next_value_list in enumerate(master_iterator):
                    for name, value in zip(iterator_names, next_value_list):
                        context.interpreter.register_variable(name, value)
                    rc = self._generate_row(output_stream, context, i)

        return rc  # return last row

    @contextmanager
    def exception_handling(self, message: str):
        try:
            yield
        except DataGenError:
            raise
        except Exception as e:
            raise DataGenError(
                f"{message} : {str(e)}", self.filename, self.line_num
            ) from e

    def _evaluate_count(self, context: RuntimeContext) -> int:
        """Evaluate the count expression to an integer"""
        if not self.count_expr:
            return 1
        else:
            try:
                return int(float(cast(str, self.count_expr.render(context))))
            except (ValueError, TypeError) as e:
                raise DataGenValueError(
                    f"Cannot evaluate {self.count_expr.definition} as number",
                    self.count_expr.filename,
                    self.count_expr.line_num,
                ) from e

    @property
    def name(self) -> str:
        name = self.tablename
        if self.nickname:
            name += f" ({self.nickname})"
        return name

    @property
    def id(self):
        return id(self)

    def _evaluate_for_each(self, context: RuntimeContext) -> LoopIterator:
        """Evaluate the expression to get an iterator we can iterate over"""

        def eval_to_iterator(vardef):
            val = vardef.evaluate(context)
            try:
                iterator = iter(val)
            except TypeError:  # pragma: no cover
                raise DataGenError(
                    f"Object created by {vardef.varname} is not iterable: {val}"
                )
            return LoopIterator(vardef.varname, iterator)

        with self.exception_handling("Cannot evaluate `for_each` definition"):
            return eval_to_iterator(self.for_each_expr)

    def _generate_row(
        self, output_stream, context: RuntimeContext, index: int
    ) -> ObjectRow:
        """Generate an individual row"""
        id = context.generate_id(self.nickname)
        row = {"id": id}

        # add a column keeping track of what update_key was specified by
        # the template. This allows multiple templates to have different
        # update_keys.
        if self.update_key:
            row["_sf_update_key"] = self.update_key
        sobj = ObjectRow(self.tablename, row, index)

        context.register_object(sobj, self.nickname, self.just_once)

        self._generate_fields(context, row)

        context.remember_row(
            self.tablename,
            self.nickname,
            row,
        )

        with self.exception_handling("Cannot write row"):
            if not self.tablename.startswith("__"):
                output_stream.write_row(self.tablename, context.filter_row_values(row))

        context.interpreter.loop_over_templates_once(self.friends, True)
        return sobj

    def _generate_fields(self, context: RuntimeContext, row: Dict) -> None:
        """Generate all of the fields of a row"""
        for field in self.fields:
            with self.exception_handling("Problem rendering value"):
                value = field.generate_value(context)
                if isinstance(value, PluginResultIterator):
                    value = value.next()
                row[field.name] = value

                self._check_type(field, row[field.name], context)

    def _check_type(self, field, generated_value, context: RuntimeContext):
        """Check the type of a field value"""
        if not isinstance(generated_value, FieldValue.__args__):
            raise DataGenValueError(
                f"Field '{field.name}' generated unexpected object: {generated_value} {type(generated_value)}",
                self.filename,
                self.line_num,
            )

    def execute(
        self, interp: Interpreter, context: RuntimeContext, continuing: bool
    ) -> Optional[ObjectRow]:
        should_skip = self.just_once and continuing
        if not should_skip:
            self.generate_rows(interp.output_stream, interp.current_context)


class SimpleValue(FieldDefinition):
    """A value with no sub-structure (although it could hold a formula)

    - object: abc
      fields:
         fieldname: XXXXX
         fieldname2: ${{XXXXX}}
         fieldname3: 42
    """

    def __init__(self, definition: Scalar, filename: str, line_num: int):
        self.filename = filename
        self.line_num = line_num
        self.definition: Scalar = definition
        assert isinstance(filename, str)
        assert isinstance(line_num, int), line_num
        self._evaluator = None

    def evaluator(self, context):
        """Populate the evaluator property once."""
        if self._evaluator is None:
            if isinstance(self.definition, str):
                with self.exception_handling("Cannot parse value {}", self.definition):
                    self._evaluator = context.get_evaluator(self.definition)
            else:
                self._evaluator = False
        return self._evaluator

    def render(self, context: RuntimeContext) -> FieldValue:
        """Render the value: rendering a template if necessary."""
        old_context_identifier = context.unique_context_identifier
        context.unique_context_identifier = str(id(self))
        evaluator = self.evaluator(context)
        if evaluator:
            try:
                val = evaluator(context)
                if hasattr(val, "render"):
                    val = val.render()
            except jinja2.exceptions.UndefinedError as e:
                raise DataGenNameError(e.message, self.filename, self.line_num) from e
            except Exception as e:
                raise DataGenValueError(str(e), self.filename, self.line_num) from e
        else:
            val = self.definition
        context.unique_context_identifier = old_context_identifier
        if isinstance(val, str) and not context.interpreter.native_types:
            val = look_for_number(val)
        return val

    def __repr__(self):
        return f"<{self.__class__.__name__ , self.definition}>"


class StructuredValue(FieldDefinition):
    """A value with substructure which will call a handler function.

    - object: abc
      fields:
        fieldname:
            - reference:
                foo
        fieldname2:
            - random_number:
                min: 10
                max: 20
        fieldname3:
            - reference:
                ..."""

    def __init__(self, function_name, args, filename, line_num):
        self.function_name = function_name
        self.filename = filename
        self.line_num = line_num
        if isinstance(args, list):  # lists will represent your arguments
            self.args = args
            self.kwargs = {}
        elif isinstance(args, dict):  # dicts will represent named arguments
            self.args = []
            self.kwargs = args
        else:  # scalars will be turned into a one-argument list
            self.args = [args]
            self.kwargs = {}
        self.unique_context_identifier = str(id(self))

    def render(self, context: RuntimeContext) -> FieldValue:
        context.unique_context_identifier = self.unique_context_identifier
        if "." in self.function_name:
            objname, method, *rest = self.function_name.split(".")
            if rest:
                raise DataGenSyntaxError(
                    f"Function names should have only one '.' in them: {self.function_name}",
                    self.filename,
                    self.line_num,
                )
            obj = context.field_vars().get(objname)
            if not obj:
                raise DataGenNameError(
                    f"Cannot find definition for: {objname}",
                    self.filename,
                    self.line_num,
                )
            try:
                func = getattr(obj, method)
            except AttributeError:
                # clean up the error message a bit
                raise AttributeError(
                    f"'{objname}' plugin exposes no attribute '{method}'"
                )
            if not func:
                raise DataGenNameError(
                    f"Cannot find definition for: {method} on {objname}",
                    self.filename,
                    self.line_num,
                )
            value = evaluate_function(func, self.args, self.kwargs, context)
        else:
            try:
                func = context.executable_blocks()[self.function_name]
            except KeyError:
                raise DataGenNameError(
                    f"Cannot find function named {self.function_name} to handle field value",
                    self.filename,
                    self.line_num,
                )

            with self.exception_handling(
                "Cannot evaluate function `{}`:\n {e}", [self.function_name]
            ):
                value = evaluate_function(func, self.args, self.kwargs, context)

        return value

    def __repr__(self):
        return (
            f"<StructuredValue: {self.function_name} (*{self.args}, **{self.kwargs})>"
        )


class FieldFactory:
    """Represents a single data field (name, value) to be rendered

    - object:
      fields:
        name: value   # this part
    """

    def __init__(self, name: str, definition: Definition, filename: str, line_num: int):
        self.name = name
        self.filename = filename
        self.line_num = line_num
        self.definition = definition

    def generate_value(self, context) -> FieldValue:
        try:
            return self.definition.render(context)
        except Exception as e:
            raise fix_exception(
                "Problem rendering field {}:\n {e}", self, e, [self.name]
            ) from e

    def __repr__(self):
        return f"<{self.__class__.__name__, self.name, self.definition.__class__.__name__}>"


Statement = Union[ObjectTemplate, VariableDefinition]
