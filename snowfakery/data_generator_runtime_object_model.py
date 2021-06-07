from abc import abstractmethod, ABC
from .data_generator_runtime import evaluate_function, RuntimeContext, Interpreter
from .object_rows import ObjectRow, ObjectReference
from contextlib import contextmanager
from typing import Union, Dict, Sequence, Optional, cast
from .utils.template_utils import look_for_number

import jinja2

from .data_gen_exceptions import (
    DataGenError,
    DataGenNameError,
    DataGenSyntaxError,
    DataGenValueError,
    fix_exception,
)
from .plugins import Scalar, PluginResult

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
        except DataGenError as e:
            raise fix_exception(message, self, e) from e
        except Exception as e:
            message = message.format(*args, **kwargs)
            raise DataGenError(
                f"{message} : {str(e)}", self.filename, self.line_num
            ) from e


class VariableDefinition:
    """Defines a mutable variable. Like:

    - var: Foo
      value: Bar
    """

    # TODO: Add an example

    tablename = None

    def __init__(
        self, filename: str, line_num: int, varname: str, expression: Definition
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
        just_once: bool = False,
        fields: Sequence = (),
        friends: Sequence = (),
    ):
        self.tablename = tablename
        self.nickname = nickname
        self.count_expr = count_expr
        self.just_once = just_once
        self.filename = filename
        self.line_num = line_num
        self.fields = fields
        self.friends = friends

    def render(self, context: RuntimeContext) -> Optional[ObjectRow]:
        return self.generate_rows(context.output_stream, context)

    def generate_rows(
        self, output_stream, parent_context: RuntimeContext
    ) -> Optional[ObjectRow]:
        """Generate several rows"""
        rc = None
        with parent_context.child_context(self) as context:
            count = self._evaluate_count(context)
            with self.exception_handling(f"Cannot generate {self.name}"):
                for i in range(count):
                    rc = self._generate_row(output_stream, context, i)

        return rc  # return last row

    @contextmanager
    def exception_handling(self, message: str):
        try:
            yield
        except DataGenError:
            raise
        except Exception as e:
            raise DataGenError(f"{message} : {str(e)}", self.filename, self.line_num)

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

    def _generate_row(
        self, output_stream, context: RuntimeContext, index: int
    ) -> ObjectRow:
        """Generate an individual row"""
        id = context.generate_id(self.nickname)
        row = {"id": id}
        sobj = ObjectRow(self.tablename, row, index)

        context.register_object(sobj, self.nickname, self.just_once)

        self._generate_fields(context, row)

        with self.exception_handling("Cannot write row"):
            self.register_row_intertable_references(row, context)
            if not self.tablename.startswith("__"):
                output_stream.write_row(self.tablename, row)

        context.interpreter.loop_over_templates_once(self.friends, True)
        return sobj

    def _generate_fields(self, context: RuntimeContext, row: Dict) -> None:
        """Generate all of the fields of a row"""
        for field in self.fields:
            with self.exception_handling("Problem rendering value"):
                row[field.name] = field.generate_value(context)
                self._check_type(field, row[field.name], context)

    def _check_type(self, field, generated_value, context: RuntimeContext):
        """Check the type of a field value"""
        if not isinstance(generated_value, FieldValue.__args__):
            raise DataGenValueError(
                f"Field '{field.name}' generated unexpected object: {generated_value} {type(generated_value)}",
                self.filename,
                self.line_num,
            )

    def register_row_intertable_references(
        self, row: dict, context: RuntimeContext
    ) -> None:
        """Before serializing we need to convert objects to flat ID integers."""
        for fieldname, fieldvalue in row.items():
            if isinstance(fieldvalue, (ObjectRow, ObjectReference)):
                context.register_intertable_reference(
                    self.tablename, fieldvalue._tablename, fieldname
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
        context.unique_context_identifier = str(id(self))
        evaluator = self.evaluator(context)
        if evaluator:
            try:
                val = evaluator(context)
            except jinja2.exceptions.UndefinedError as e:
                raise DataGenNameError(e.message, self.filename, self.line_num) from e
            except Exception as e:
                raise DataGenValueError(str(e), self.filename, self.line_num) from e
        else:
            val = self.definition
        return look_for_number(val) if isinstance(val, str) else val

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

    def render(self, context: RuntimeContext) -> FieldValue:
        context.unique_context_identifier = id(self)
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
                    f"'{objname}' plugin exposes no attribute '{method}"
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
                "Cannot evaluate function {}", self.function_name
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
                f"Problem rendering field {self.name}:\n {str(e)}", self, e
            ) from e

    def __repr__(self):
        return f"<{self.__class__.__name__, self.name, self.definition.__class__.__name__}>"


Statement = Union[ObjectTemplate, VariableDefinition]
