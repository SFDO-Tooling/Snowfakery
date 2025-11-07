"""Recipe validation framework.

This module provides semantic validation for Snowfakery recipes,
catching errors before runtime execution.
"""

from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from datetime import datetime, timezone
from faker import Faker
import jinja2
from jinja2 import nativetypes
from jinja2.sandbox import SandboxedEnvironment

from snowfakery.utils.validation_utils import (
    get_fuzzy_match,
    resolve_value,
    with_mock_context,
    validate_and_check_errors,
)
from snowfakery.data_generator_runtime_object_model import (
    ObjectTemplate,
    VariableDefinition,
    FieldFactory,
    ForEachVariableDefinition,
    StructuredValue,
    SimpleValue,
)
from snowfakery.template_funcs import StandardFuncs
from snowfakery.fakedata.faker_validators import FakerValidators
from snowfakery.fakedata.fake_data_generator import FakeNames


class SandboxedNativeEnvironment(SandboxedEnvironment, nativetypes.NativeEnvironment):
    """Jinja2 environment that combines sandboxing security with native type preservation.

    This class provides:
    - Security restrictions from SandboxedEnvironment (blocks dangerous operations)
    - Native Python type preservation from NativeEnvironment (returns int, bool, list, etc.)

    Used during validation to safely execute Jinja templates while maintaining
    type compatibility with Snowfakery's runtime behavior.
    """

    pass


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

        # Jinja execution support
        self.interpreter: Optional[Any] = None  # Interpreter instance
        self.current_template: Optional[
            Any
        ] = None  # Current ObjectTemplate/VariableDefinition being validated
        self.faker_instance: Optional[
            Any
        ] = None  # Faker instance for executing providers

        # Variable value cache to prevent recursion during evaluation
        self._variable_cache: Dict[str, Any] = {}
        self._evaluating: set = set()  # Track variables currently being evaluated

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

    def get_evaluator(self, definition: str):
        """Get Jinja evaluator (same as RuntimeContext).

        Args:
            definition: The Jinja template string

        Returns:
            A callable that evaluates the template, or a lambda returning the string if no Jinja
        """
        if not self.interpreter:
            raise RuntimeError("Interpreter not set in ValidationContext")
        return self.interpreter.template_evaluator_factory.get_evaluator(definition)

    def field_vars(self):
        """Build validation namespace for Jinja execution.

        Returns a dict mimicking the namespace available at runtime, but with mock values.
        This allows Jinja templates to be executed and validated.
        """
        return self._build_validation_namespace()

    def _build_validation_namespace(self):
        """Build namespace with mock values for all available names."""
        if not self.interpreter:
            raise RuntimeError("Interpreter not set in ValidationContext")

        namespace = {}

        # 1. Built-in variables (from EvaluationNamespace.simple_field_vars)
        namespace["id"] = 1
        namespace["count"] = 1
        namespace["child_index"] = 0
        namespace["today"] = self.interpreter.globals.today
        namespace["now"] = datetime.now(timezone.utc)
        namespace["template"] = self.current_template  # Current statement

        # 2. User variables (with mock values)
        for var_name in self.available_variables.keys():
            # Skip variables currently being evaluated to prevent recursion
            if var_name not in self._evaluating:
                namespace[var_name] = self._get_mock_value_for_variable(var_name)

        # 3. Objects (with field-aware mocks)
        for obj_name in self.available_objects.keys():
            namespace[obj_name] = self._create_mock_object(obj_name)
        for nickname in self.available_nicknames.keys():
            namespace[nickname] = self._create_mock_object(nickname)

        # 4. Functions (with validation wrappers)
        for func_name, validator in self.available_functions.items():
            namespace[func_name] = self._create_validation_function(
                func_name, validator
            )

        # 5. Plugins (with validation wrappers)
        for plugin_name, plugin_instance in self.interpreter.plugin_instances.items():
            namespace[plugin_name] = self._create_mock_plugin(
                plugin_name, plugin_instance
            )

        # 6. Faker (mock with provider validation)
        namespace["fake"] = self._create_mock_faker()

        # 7. Options
        namespace.update(self.interpreter.options)

        return namespace

    def _get_mock_value_for_variable(self, var_name):
        """Get value for a variable.

        Args:
            var_name: Name of the variable

        Returns:
            The variable's evaluated value
        """
        # Check cache first
        if var_name in self._variable_cache:
            return self._variable_cache[var_name]

        # Mark as evaluating (to skip in namespace building and prevent recursion)
        self._evaluating.add(var_name)

        try:
            var_def = self.available_variables.get(var_name)
            if var_def and hasattr(var_def, "expression"):
                expression = var_def.expression

                # If it's a SimpleValue, check if it's literal or Jinja
                if isinstance(expression, SimpleValue):
                    definition = expression.definition

                    # If it's a Jinja template, evaluate it
                    if isinstance(definition, str) and (
                        "${{" in definition or "${%" in definition
                    ):
                        result = validate_jinja_template_by_execution(
                            definition, expression.filename, expression.line_num, self
                        )
                        if result is not None:
                            self._variable_cache[var_name] = result
                            return result
                    else:
                        # Literal value
                        self._variable_cache[var_name] = definition
                        return definition

                # If it's a StructuredValue, resolve it
                if isinstance(expression, StructuredValue):
                    resolved = resolve_value(expression, self)
                    if resolved is not None:
                        self._variable_cache[var_name] = resolved
                        return resolved

            # Fall back to mock value if variable not found
            mock_value = f"<mock_variable_{var_name}>"
            self._variable_cache[var_name] = mock_value
            return mock_value
        finally:
            # Remove from evaluating set
            self._evaluating.discard(var_name)

    def _create_mock_object(self, name):
        """Create mock object that validates field access.

        Args:
            name: Object name or nickname

        Returns:
            MockObjectRow instance with field validation
        """
        # Get the actual ObjectTemplate
        obj_template = self.available_objects.get(name) or self.available_nicknames.get(
            name
        )

        class MockObjectRow:
            def __init__(self, template, context):
                self.id = 1
                self._template = template
                self._name = name
                self._context = context

                # Extract actual field names and definitions from template
                if template and hasattr(template, "fields"):
                    self._field_names = {
                        f.name for f in template.fields if isinstance(f, FieldFactory)
                    }
                    # Build field definition map
                    self._field_definitions = {
                        f.name: f.definition
                        for f in template.fields
                        if isinstance(f, FieldFactory)
                    }
                else:
                    self._field_names = set()
                    self._field_definitions = {}

            def __getattr__(self, attr):
                # Validate field exists
                if attr.startswith("_"):
                    raise AttributeError(f"'{attr}' not found")

                # If we have field information, validate the attribute exists
                if self._template and hasattr(self._template, "fields"):
                    if attr not in self._field_names:
                        raise AttributeError(
                            f"Object '{self._name}' has no field '{attr}'. "
                            f"Available fields: {', '.join(sorted(self._field_names)) if self._field_names else 'none'}"
                        )

                # Try to resolve the field value
                if attr in self._field_definitions:
                    from snowfakery.utils.validation_utils import resolve_value

                    field_def = self._field_definitions[attr]
                    resolved = resolve_value(field_def, self._context)
                    if resolved is not None:
                        return resolved

                # Fall back to mock value if we can't resolve
                return f"<mock_{self._name}.{attr}>"

        return MockObjectRow(obj_template, self)

    def _create_validated_wrapper(
        self, func_name, validator, actual_func_getter, is_plugin=False
    ):
        """Create a validation wrapper that validates before executing.

        Args:
            func_name: Full function name (e.g., "random_number" or "StatisticalDistributions.normal")
            validator: Validator function to call
            actual_func_getter: Callable that returns the actual function to execute, or None
            is_plugin: Whether this is a plugin function (requires mock context)

        Returns:
            Wrapper function that validates and conditionally executes
        """

        def validation_wrapper(*args, **kwargs):
            # Create synthetic StructuredValue
            sv = StructuredValue(
                func_name,
                kwargs if kwargs else list(args),
                self.current_template.filename
                if self.current_template
                else "<unknown>",
                self.current_template.line_num if self.current_template else 0,
            )

            # Call validator and track if errors were added
            try:
                validation_added_errors = validate_and_check_errors(
                    self, validator, sv, self
                )
            except Exception as e:
                self.add_error(
                    f"Function '{func_name}' validation failed: {str(e)}",
                    sv.filename,
                    sv.line_num,
                )
                validation_added_errors = True

            # If validation added errors, don't attempt execution
            if validation_added_errors:
                return f"<mock_function_{func_name}>"

            # Try to execute the actual function to get a real value
            try:
                actual_func = actual_func_getter()
                if actual_func and callable(actual_func):
                    # For plugin functions, we need to set up mock context
                    if is_plugin:
                        from snowfakery.utils.validation_utils import with_mock_context

                        with with_mock_context(self):
                            return actual_func(*args, **kwargs)
                    else:
                        return actual_func(*args, **kwargs)
            except Exception:
                # Could not execute function, return mock value
                pass

            return f"<mock_function_{func_name}>"

        return validation_wrapper

    def _create_validation_function(self, func_name, validator):
        """Create wrapper that validates when called from Jinja.

        Args:
            func_name: Name of the function
            validator: Validator function to call

        Returns:
            Wrapper function that validates and returns mock value
        """

        def get_standard_func():
            if self.interpreter and func_name in self.interpreter.standard_funcs:
                return self.interpreter.standard_funcs[func_name]
            return None

        return self._create_validated_wrapper(func_name, validator, get_standard_func)

    def _create_mock_plugin(self, plugin_name, plugin_instance):
        """Create mock plugin namespace that validates function calls.

        Args:
            plugin_name: Name of the plugin (e.g., "StatisticalDistributions")
            plugin_instance: The actual plugin instance

        Returns:
            Mock plugin namespace with validated function wrappers
        """
        plugin_funcs = plugin_instance.custom_functions()

        class MockPlugin:
            def __init__(self, plugin_name, plugin_funcs, context):
                self._plugin_name = plugin_name
                self._plugin_funcs = plugin_funcs
                self._context = context

            def __getattr__(self, func_attr):
                # Build full function name with plugin namespace
                func_full_name = f"{self._plugin_name}.{func_attr}"

                # Check if this function has a validator
                if func_full_name in self._context.available_functions:
                    validator = self._context.available_functions[func_full_name]

                    # Create function getter for this specific plugin method
                    def get_plugin_func():
                        return getattr(self._plugin_funcs, func_attr, None)

                    # Use shared validation wrapper (with plugin context support)
                    return self._context._create_validated_wrapper(
                        func_full_name, validator, get_plugin_func, is_plugin=True
                    )
                else:
                    # No validator, return actual function
                    return getattr(self._plugin_funcs, func_attr)

        return MockPlugin(plugin_name, plugin_funcs, self)

    def _create_mock_faker(self):
        """Create mock Faker that validates provider names and parameters.

        Returns:
            MockFaker instance that validates and executes Faker providers
        """

        class MockFaker:
            def __init__(self, context):
                self.context = context
                # Create validator instance for parameter validation
                self.validator = (
                    FakerValidators(context.faker_instance, context.faker_providers)
                    if context.faker_instance
                    else None
                )

            def __getattr__(self, provider_name):
                # Validate provider exists using shared validator
                if self.validator:
                    filename = (
                        self.context.current_template.filename
                        if self.context.current_template
                        else None
                    )
                    line_num = (
                        self.context.current_template.line_num
                        if self.context.current_template
                        else None
                    )
                    self.validator.validate_provider_name(
                        provider_name, self.context, filename, line_num
                    )

                # Return wrapper that validates parameters and executes method
                def validated_provider(*args, **kwargs):
                    # Validate parameters using introspection
                    if self.validator:
                        self.validator.validate_provider_call(
                            provider_name, args, kwargs, self.context
                        )

                    # Try to execute the actual Faker method
                    try:
                        if self.context.faker_instance:
                            actual_method = getattr(
                                self.context.faker_instance, provider_name, None
                            )
                            if actual_method and callable(actual_method):
                                return actual_method(*args, **kwargs)
                    except Exception:
                        # Execution failed, return mock value
                        pass

                    # Return mock value as fallback
                    return f"<fake_{provider_name}>"

                return validated_provider

        return MockFaker(self)


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

    # Add plugin validators
    for plugin in plugins:
        plugin_name = plugin.__class__.__name__  # e.g., "UniqueId", "Math", etc.

        if hasattr(plugin, "Validators"):
            validators = plugin.Validators
            functions = plugin.Functions if hasattr(plugin, "Functions") else None

            for attr in dir(validators):
                if attr.startswith("validate_"):
                    func_name = attr.replace("validate_", "")
                    validator = getattr(validators, attr)

                    # Register with plugin namespace prefix for StructuredValue access
                    # e.g., "UniqueId.NumericIdGenerator"
                    registry[f"{plugin_name}.{func_name}"] = validator

                    # Check if there's an alias without trailing underscore
                    if functions and func_name.endswith("_"):
                        alias_name = func_name[:-1]
                        if hasattr(functions, alias_name):
                            registry[f"{plugin_name}.{alias_name}"] = validator

    # Add Faker validator (special case - StructuredValue syntax: fake: provider_name)
    registry["fake"] = FakerValidators.validate_fake

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
    context.available_functions = build_function_registry(
        interpreter.plugin_instances.values()
    )

    # Store interpreter reference for Jinja execution
    context.interpreter = interpreter

    # Extract method names from faker by creating a Faker instance with the providers
    # This replicates what FakeData does at runtime (see fake_data_generator.py:173-177)
    faker_instance = Faker()

    # Add custom providers to the faker instance
    for provider in interpreter.faker_providers:
        faker_instance.add_provider(provider)

    # Add FakeNames to override standard Faker methods with Snowfakery's custom signatures
    # (e.g., email(matching=True) instead of standard Faker's email(safe=True, domain=None))
    # This matches what FakeData.__init__ does at runtime
    fake_names = FakeNames(faker_instance, faker_context=None)
    faker_instance.add_provider(fake_names)

    # Store faker instance in context for execution
    context.faker_instance = faker_instance

    # Extract all callable methods from the faker instance
    faker_method_names = set()
    for name in dir(faker_instance):
        if name.startswith("_"):
            continue
        try:
            attr = getattr(faker_instance, name, None)
            if callable(attr):
                faker_method_names.add(name)
        except (TypeError, AttributeError):
            # Skip attributes that raise errors (e.g., seed)
            continue
    context.faker_providers = faker_method_names

    # Create Jinja environment with SandboxedNativeEnvironment
    context.jinja_env = SandboxedNativeEnvironment(
        block_start_string="${%",
        block_end_string="%}",
        variable_start_string="${{",
        variable_end_string="}}",
        undefined=jinja2.StrictUndefined,
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

        # Set current template for Jinja context
        context.current_template = statement

        # Validate statement (can only see items defined before this point in sequential registries)
        validate_statement(statement, context)

        # Clear current template
        context.current_template = None

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


def validate_jinja_template_by_execution(
    template_str: str, filename: str, line_num: int, context: ValidationContext
) -> Optional[Any]:
    """Validate Jinja template by executing it in validation context.

    This function actually executes the Jinja template in a mock context,
    catching any errors that would occur at runtime.

    Args:
        template_str: The Jinja template string
        filename: Source file for error reporting
        line_num: Line number for error reporting
        context: Validation context

    Returns:
        The resolved value if execution succeeds, None if it fails
    """
    # 1. Syntax checks
    try:
        context.jinja_env.parse(template_str)
    except jinja2.TemplateSyntaxError as e:
        context.add_error(f"Jinja syntax error: {str(e)}", filename, line_num)
        return None

    # 2. Check if template contains Jinja
    if not ("${{" in template_str or "${%" in template_str):
        # No Jinja template, just return the literal string
        return template_str

    # 3. Parse and execute template using our strict Jinja environment
    try:
        namespace_dict = {}
        with with_mock_context(context, namespace_dict):
            namespace = context.field_vars()
            # Render the template (mock context is still active)
            template = context.jinja_env.from_string(template_str)
            result = template.render(namespace)
            # NativeEnvironment returns a lazy object - force evaluation to catch errors
            bool(result)  # Force evaluation
            return result
    except jinja2.exceptions.UndefinedError as e:
        # Variable or name not found
        error_msg = getattr(e, "message", str(e))

        # Simplify error messages about MockObjectRow to be more user-friendly
        # MockObjectRow is an internal validation class, users shouldn't see it in error messages
        # Example: "'MockObjectRow' object has no attribute 'foo'" -> "Object has no attribute 'foo'"
        if (
            error_msg
            and "MockObjectRow object" in error_msg
            and "has no attribute" in error_msg
        ):
            # Extract just the attribute name
            import re

            match = re.search(r"has no attribute '(\w+)'", error_msg)
            if match:
                attr_name = match.group(1)
                error_msg = f"Object has no attribute '{attr_name}'"

        context.add_error(
            f"Jinja template error: {error_msg}",
            filename,
            line_num,
        )
        return None
    except AttributeError as e:
        # Attribute access error (e.g., object.nonexistent_field)
        context.add_error(
            f"Jinja template attribute error: {str(e)}", filename, line_num
        )
        return None
    except TypeError as e:
        # Type error (e.g., calling non-callable, wrong arguments)
        context.add_error(f"Jinja template type error: {str(e)}", filename, line_num)
        return None
    except Exception as e:
        # Any other runtime error
        context.add_error(
            f"Jinja template evaluation error: {str(e)}", filename, line_num
        )
        return None


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
            validate_jinja_template_by_execution(
                field_def.definition, field_def.filename, field_def.line_num, context
            )
