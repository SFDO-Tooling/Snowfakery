"""Recipe validation framework.

This module provides semantic validation for Snowfakery recipes,
catching errors before runtime execution.
"""

from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass

import jinja2

from snowfakery.utils.validation_utils import get_fuzzy_match
from snowfakery.data_generator_runtime_object_model import (
    ObjectTemplate,
    VariableDefinition,
    FieldFactory,
    ForEachVariableDefinition,
    StructuredValue,
    SimpleValue,
)
from snowfakery.template_funcs import StandardFuncs


@dataclass
class ValidationError:
    """Represents a validation error."""

    message: str
    filename: Optional[str] = None
    line_num: Optional[int] = None

    def __str__(self):
        location = ""
        if self.filename:
            location = f"{self.filename}"
            if self.line_num:
                location += f":{self.line_num}"
            location += ": "
        return f"{location}Error: {self.message}"


@dataclass
class ValidationWarning:
    """Represents a validation warning."""

    message: str
    filename: Optional[str] = None
    line_num: Optional[int] = None

    def __str__(self):
        location = ""
        if self.filename:
            location = f"{self.filename}"
            if self.line_num:
                location += f":{self.line_num}"
            location += ": "
        return f"{location}Warning: {self.message}"


class ValidationResult:
    """Collects validation errors and warnings."""

    def __init__(
        self,
        errors: Optional[List[ValidationError]] = None,
        warnings: Optional[List[ValidationWarning]] = None,
    ):
        self.errors = errors if errors is not None else []
        self.warnings = warnings if warnings is not None else []

    def has_errors(self) -> bool:
        """Check if any errors were found."""
        return len(self.errors) > 0

    def has_warnings(self) -> bool:
        """Check if any warnings were found."""
        return len(self.warnings) > 0

    def get_summary(self) -> str:
        """Get a human-readable summary of validation results."""
        lines = []

        if self.errors:
            lines.append("\nValidation Errors:")
            for i, error in enumerate(self.errors, 1):
                lines.append(f"  {i}. {error.message}")
                if error.filename:
                    location = f"     at {error.filename}"
                    if error.line_num:
                        location += f":{error.line_num}"
                    lines.append(location)

        if self.warnings:
            lines.append("\nValidation Warnings:")
            for i, warning in enumerate(self.warnings, 1):
                lines.append(f"  {i}. {warning.message}")
                if warning.filename:
                    location = f"     at {warning.filename}"
                    if warning.line_num:
                        location += f":{warning.line_num}"
                    lines.append(location)

        if not self.errors and not self.warnings:
            lines.append("\n✓ Validation passed with no errors or warnings.")

        return "\n".join(lines)

    def __str__(self):
        return self.get_summary()


class ValidationContext:
    """Central context for validation with registries and error collection."""

    def __init__(self):
        # Function and provider registries
        self.available_functions: Dict[str, Callable] = {}
        self.faker_providers: set = set()

        # Dual object registries:
        # 1. ALL objects (pre-registered, for reference/random_reference validation)
        self.all_objects: Dict[str, Any] = {}  # All object names (forward refs allowed)
        self.all_nicknames: Dict[str, Any] = {}  # All nicknames (forward refs allowed)

        # 2. Sequential objects (registered as encountered, for Jinja ${{ObjectName.field}})
        self.available_objects: Dict[
            str, Any
        ] = {}  # Objects seen so far (order matters)
        self.available_nicknames: Dict[
            str, Any
        ] = {}  # Nicknames seen so far (order matters)

        # Variable registry (sequential, order matters)
        self.available_variables: Dict[
            str, Any
        ] = {}  # variable name -> VariableDefinition

        # Field registry within current object (for tracking field definition order)
        self.current_object_fields: Dict[
            str, Any
        ] = {}  # Fields defined so far in current object

        # Jinja environment (for syntax validation only)
        # Will be initialized in validate_recipe before any validation
        self.jinja_env: Any = None  # Jinja2 environment (jinja2.Environment)

        # Error collection
        self.errors: List[ValidationError] = []
        self.warnings: List[ValidationWarning] = []

    def add_error(
        self,
        message: str,
        filename: Optional[str] = None,
        line_num: Optional[int] = None,
    ):
        """Add a validation error."""
        self.errors.append(ValidationError(message, filename, line_num))

    def add_warning(
        self,
        message: str,
        filename: Optional[str] = None,
        line_num: Optional[int] = None,
    ):
        """Add a validation warning."""
        self.warnings.append(ValidationWarning(message, filename, line_num))

    def resolve_variable(self, name: str) -> Optional[Any]:
        """Look up a variable definition by name."""
        return self.available_variables.get(name)

    def resolve_object(
        self, name: str, allow_forward_ref: bool = False
    ) -> Optional[Any]:
        """Look up an object by name or nickname.

        Args:
            name: Object name or nickname to look up
            allow_forward_ref: If True, use all_objects (for reference/random_reference).
                              If False, use available_objects (for Jinja/sequential access).
        """
        if allow_forward_ref:
            # Use all_objects/all_nicknames (forward references allowed)
            if name in self.all_objects:
                return self.all_objects[name]
            if name in self.all_nicknames:
                return self.all_nicknames[name]
        else:
            # Use available_objects/available_nicknames (sequential, order matters)
            if name in self.available_objects:
                return self.available_objects[name]
            if name in self.available_nicknames:
                return self.available_nicknames[name]
        return None

    def get_object_count(self, obj_name: str) -> Optional[int]:
        """Get the literal count for an object if available."""
        obj = self.available_objects.get(obj_name)
        if obj and hasattr(obj, "count_expr"):
            # Try to extract literal count
            count_expr = obj.count_expr
            if isinstance(count_expr, int):
                return count_expr
            # For POC, we only handle literal integers
        return None


def build_function_registry(plugins) -> Dict[str, Callable]:
    """Build registry mapping function names to validators.

    This maps actual function names (as they appear in recipes) to their validators.
    It handles cases where functions have Python-incompatible names (e.g., "if" -> "if_").

    Args:
        plugins: List of plugin objects that may contain Validators classes

    Returns:
        Dictionary mapping function names to their validator functions
    """
    registry = {}

    # Add standard function validators
    if hasattr(StandardFuncs, "Validators"):
        validators = StandardFuncs.Validators
        functions = (
            StandardFuncs.Functions if hasattr(StandardFuncs, "Functions") else None
        )

        for attr in dir(validators):
            if attr.startswith("validate_"):
                func_name = attr.replace("validate_", "")
                validator = getattr(validators, attr)
                registry[func_name] = validator

                # Check if there's an alias without trailing underscore (e.g., "if" for "if_")
                if functions and func_name.endswith("_"):
                    alias_name = func_name[:-1]
                    if hasattr(functions, alias_name):
                        # The Functions class has the alias (e.g., "if"), register it
                        registry[alias_name] = validator

    # Add plugin validators (future enhancement)
    for plugin in plugins:
        if hasattr(plugin, "Validators"):
            validators = plugin.Validators
            functions = plugin.Functions if hasattr(plugin, "Functions") else None

            for attr in dir(validators):
                if attr.startswith("validate_"):
                    func_name = attr.replace("validate_", "")
                    validator = getattr(validators, attr)
                    registry[func_name] = validator

                    # Check if there's an alias without trailing underscore
                    if functions and func_name.endswith("_"):
                        alias_name = func_name[:-1]
                        if hasattr(functions, alias_name):
                            registry[alias_name] = validator

    return registry


def is_name_available(name: str, context: ValidationContext) -> bool:
    """Check if a name is available in the validation context.

    A name is considered available if it exists as:
    - A variable (in available_variables)
    - A function (in available_functions)
    - An object or nickname (in available_objects/available_nicknames)
    - A faker provider (in faker_providers)

    Args:
        name: The name to check
        context: The validation context

    Returns:
        True if the name is available, False otherwise
    """
    return (
        name in context.available_variables
        or name in context.available_functions
        or name in context.available_objects
        or name in context.available_nicknames
        or name in context.faker_providers
    )


def validate_recipe(parse_result, interpreter, options) -> ValidationResult:
    """Main entry point for recipe validation.

    Args:
        parse_result: The parsed recipe (ParseResult object)
        interpreter: Full Interpreter instance (with runtime context)
        options: User options passed to the recipe

    Returns:
        ValidationResult containing errors and warnings
    """
    # Build context
    context = ValidationContext()
    context.available_functions = build_function_registry(interpreter.plugin_instances)

    # Extract method names from faker provider instances
    faker_method_names = set()
    for provider in interpreter.faker_providers:
        # Get all public methods from the provider
        faker_method_names.update(
            [
                name
                for name in dir(provider)
                if not name.startswith("_") and callable(getattr(provider, name, None))
            ]
        )
    context.faker_providers = faker_method_names

    # Create Jinja environment for syntax validation
    context.jinja_env = jinja2.Environment(
        block_start_string="${%",
        block_end_string="%}",
        variable_start_string="${{",
        variable_end_string="}}",
    )

    # First pass: Pre-register ALL objects in all_objects/all_nicknames
    # This allows forward references for reference/random_reference functions
    for statement in parse_result.statements:
        if isinstance(statement, ObjectTemplate):
            context.all_objects[statement.tablename] = statement
            if statement.nickname:
                context.all_nicknames[statement.nickname] = statement

    # Second pass: Sequential validation with progressive registration
    # Variables and objects are registered as we encounter them (mimics runtime behavior)
    for statement in parse_result.statements:
        # Register in sequential registries BEFORE validating
        if isinstance(statement, ObjectTemplate):
            # Register for Jinja access (${{ObjectName.field}})
            context.available_objects[statement.tablename] = statement
            if statement.nickname:
                context.available_nicknames[statement.nickname] = statement

        elif isinstance(statement, VariableDefinition):
            # Register variable (order matters for variables)
            context.available_variables[statement.varname] = statement

        # Validate statement (can only see items defined before this point in sequential registries)
        validate_statement(statement, context)

    return ValidationResult(context.errors, context.warnings)


def validate_statement(statement, context: ValidationContext):
    """Validate a single statement (ObjectTemplate or VariableDefinition).

    Args:
        statement: An ObjectTemplate or VariableDefinition
        context: The validation context
    """
    if isinstance(statement, ObjectTemplate):
        # Clear field registry for new object
        context.current_object_fields = {}

        # Validate count expression
        if statement.count_expr:
            validate_field_definition(statement.count_expr, context)

        # Validate and register for_each expression
        if statement.for_each_expr:
            if isinstance(statement.for_each_expr, ForEachVariableDefinition):
                # Validate the iterator expression
                validate_field_definition(statement.for_each_expr.expression, context)

                # Register the loop variable so fields can reference it
                context.available_variables[
                    statement.for_each_expr.varname
                ] = statement.for_each_expr

        # Validate fields sequentially (order matters within object)
        for field in statement.fields:
            if isinstance(field, FieldFactory):
                # Validate field (can reference previously defined fields in this object)
                validate_field_definition(field.definition, context)

                # Register field so subsequent fields can reference it
                context.current_object_fields[field.name] = field

        # Recursively validate friends (nested ObjectTemplates)
        for friend in statement.friends:
            if isinstance(friend, ObjectTemplate):
                validate_statement(friend, context)

    elif isinstance(statement, VariableDefinition):
        validate_field_definition(statement.expression, context)


def validate_jinja_template(
    template_str: str, filename: str, line_num: int, context: ValidationContext
):
    """Validate Jinja template syntax only.

    Only checks that the Jinja template is syntactically valid.
    Does NOT check variable existence or execute the template.

    Args:
        template_str: The Jinja template string
        filename: Source file for error reporting
        line_num: Line number for error reporting
        context: Validation context
    """
    # Check Jinja syntax only
    try:
        context.jinja_env.parse(template_str)
    except jinja2.TemplateSyntaxError as e:
        context.add_error(f"Jinja syntax error: {str(e)}", filename, line_num)


def validate_field_definition(field_def, context: ValidationContext):
    """Validate a FieldDefinition (SimpleValue or StructuredValue).

    This function recursively validates nested StructuredValues (function calls) and
    validates Jinja templates in SimpleValues.

    Args:
        field_def: A FieldDefinition object (SimpleValue or StructuredValue)
        context: The validation context
    """
    # Check if it's a StructuredValue (function call)
    if isinstance(field_def, StructuredValue):
        func_name = field_def.function_name

        # Look up validator for this function
        if func_name in context.available_functions:
            validator = context.available_functions[func_name]
            try:
                validator(field_def, context)
            except Exception as e:
                # Catch any validator errors to avoid breaking the validation process
                context.add_error(
                    f"Internal validation error for '{func_name}': {str(e)}",
                    getattr(field_def, "filename", None),
                    getattr(field_def, "line_num", None),
                )
        else:
            # Unknown function - add error with suggestion
            suggestion = get_fuzzy_match(
                func_name, list(context.available_functions.keys())
            )
            msg = f"Unknown function '{func_name}'"
            if suggestion:
                msg += f". Did you mean '{suggestion}'?"
            context.add_error(
                msg,
                getattr(field_def, "filename", None),
                getattr(field_def, "line_num", None),
            )

        # Recursively validate nested StructuredValues in arguments
        for arg in field_def.args:
            if isinstance(arg, StructuredValue):
                validate_field_definition(arg, context)

        # Recursively validate nested StructuredValues in keyword arguments
        for key, value in field_def.kwargs.items():
            if isinstance(value, StructuredValue):
                validate_field_definition(value, context)

    # Check if it's a SimpleValue (literal or Jinja template)
    elif isinstance(field_def, SimpleValue):
        if isinstance(field_def.definition, str) and "${{" in field_def.definition:
            # It's a Jinja template - validate it
            validate_jinja_template(
                field_def.definition, field_def.filename, field_def.line_num, context
            )
