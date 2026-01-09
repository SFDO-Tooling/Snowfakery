"""Recipe validation framework.

This module provides semantic validation for Snowfakery recipes,
catching errors before runtime execution.
"""

import re
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from datetime import datetime, timezone
from dateutil.relativedelta import relativedelta
from faker import Faker
import jinja2
from jinja2 import nativetypes
from jinja2.sandbox import SandboxedEnvironment

from snowfakery.utils.validation_utils import (
    get_fuzzy_match,
    resolve_value,
    with_mock_context,
)
from snowfakery.data_generator_runtime_object_model import (
    ObjectTemplate,
    VariableDefinition,
    FieldFactory,
    ForEachVariableDefinition,
    StructuredValue,
    SimpleValue,
)
from snowfakery.plugins import PluginResultIterator
from snowfakery.template_funcs import StandardFuncs
from snowfakery.fakedata.faker_validators import FakerValidators
from snowfakery.fakedata.fake_data_generator import FakeNames
from snowfakery.utils.template_utils import StringGenerator
from snowfakery.object_rows import ObjectReference


class SandboxedNativeEnvironment(SandboxedEnvironment, nativetypes.NativeEnvironment):
    """Jinja2 environment that combines sandboxing security with native type preservation.

    This class provides:
    - Security restrictions from SandboxedEnvironment (blocks dangerous operations)
    - Native Python type preservation from NativeEnvironment (returns int, bool, list, etc.)

    Used during validation to safely execute Jinja templates while maintaining
    type compatibility with Snowfakery's runtime behavior.
    """

    def is_safe_attribute(self, obj, attr, value):
        """Override to allow access to __ prefixed temp variable fields on MockObjectRow.

        Snowfakery uses __ prefixed field names as temporary/hidden variables in recipes.
        These are legitimate field accesses, not attempts to access private Python attributes.
        """
        # Allow __ prefixed attributes on MockObjectRow objects (temp vars)
        if attr.startswith("__") and "MockObjectRow" in type(obj).__name__:
            return True
        # Fall back to default sandbox behavior for other cases
        return super().is_safe_attribute(obj, attr, value)


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
        # Line number of current field being validated
        self.current_field_line_num: Optional[int] = None
        self.faker_instance: Optional[
            Any
        ] = None  # Faker instance for executing providers

        # Variable value cache to prevent recursion during evaluation
        self._variable_cache: Dict[str, Any] = {}
        self._evaluating: set = set()  # Track variables currently being evaluated

        # StructuredValue validation cache to prevent duplicate validation
        self._structured_value_cache: Dict[int, Any] = {}  # id(sv) -> mock result

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

        # Add 'this' - mock object representing current object being created
        if self.current_template and isinstance(self.current_template, ObjectTemplate):
            namespace["this"] = self._create_this_mock()
        else:
            namespace["this"] = None

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

        # 4.5. Constants from StandardFuncs (NULL, relativedelta, etc.)
        namespace["NULL"] = None
        namespace["null"] = None
        namespace["Null"] = None
        namespace["relativedelta"] = relativedelta

        # 4.6. Python builtins (available in Jinja at runtime)
        namespace["int"] = int
        namespace["str"] = str
        namespace["float"] = float
        namespace["bool"] = bool
        namespace["len"] = len
        namespace["list"] = list
        namespace["dict"] = dict
        namespace["set"] = set
        namespace["tuple"] = tuple
        namespace["min"] = min
        namespace["max"] = max
        namespace["sum"] = sum
        namespace["abs"] = abs
        namespace["round"] = round

        # 5. Plugins (with validation wrappers)
        for plugin_name, plugin_instance in self.interpreter.plugin_instances.items():
            namespace[plugin_name] = self._create_mock_plugin(
                plugin_name, plugin_instance
            )

        # 6. Faker (mock with provider validation)
        namespace["fake"] = self._create_mock_faker()

        # 7. Options
        namespace.update(self.interpreter.options)

        # 8. Current object fields (fields defined earlier in the same object)
        for field_name in self.current_object_fields.keys():
            if field_name not in self._evaluating:
                namespace[field_name] = self._get_mock_value_for_variable(field_name)

        return namespace

    def _get_mock_value_for_variable(self, var_name):
        """Get value for a variable or field.

        Args:
            var_name: Name of the variable or field

        Returns:
            The variable's evaluated value
        """
        # Check cache first
        if var_name in self._variable_cache:
            return self._variable_cache[var_name]

        # Mark as evaluating (to skip in namespace building and prevent recursion)
        self._evaluating.add(var_name)

        try:
            # Check available_variables first, then current_object_fields
            var_def = self.available_variables.get(var_name)
            if not var_def:
                var_def = self.current_object_fields.get(var_name)

            if var_def and hasattr(var_def, "expression"):
                expression = var_def.expression
            elif var_def and hasattr(var_def, "definition"):
                # For FieldFactory, use definition instead of expression
                expression = var_def.definition
            else:
                expression = None

            if expression:

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
                        # Plugins like Dataset and Counters return iterators
                        if isinstance(resolved, PluginResultIterator):
                            try:
                                resolved = resolved.next()
                            except StopIteration:
                                resolved = None

                        if resolved is not None:
                            if isinstance(resolved, ObjectReference):
                                ref_obj_name = resolved._tablename
                                ref_obj = self.resolve_object(
                                    ref_obj_name, allow_forward_ref=False
                                )
                                if ref_obj:
                                    resolved = self._create_mock_object(ref_obj_name)

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
        is_this = name == "this"
        if is_this:
            obj_template = self.current_template
        else:
            obj_template = self.available_objects.get(
                name
            ) or self.available_nicknames.get(name)

        context = self

        class MockObjectRow:
            """Mock object that validates field access during validation."""

            def __init__(self, template, obj_name):
                self.id = 1
                self._child_index = 0
                self._template = template
                self._name = obj_name
                self._is_this = obj_name == "this"

                # Extract actual field names and definitions from template
                if template and hasattr(template, "fields"):
                    self._all_field_names = {
                        f.name for f in template.fields if isinstance(f, FieldFactory)
                    }
                    # Build field definition map
                    self._field_definitions = {
                        f.name: f.definition
                        for f in template.fields
                        if isinstance(f, FieldFactory)
                    }
                else:
                    self._all_field_names = set()
                    self._field_definitions = {}

            def __getattr__(self, attr):
                # Allow __ prefixed temp vars if they are valid fields
                # Only reject truly private attributes (single underscore internal attrs)
                # that are NOT in the accessible fields list
                if attr.startswith("_") and attr not in self._all_field_names:
                    raise AttributeError(f"'{attr}' not found")

                # For 'this': only fields defined so far are accessible
                # For object references: all fields of that object are accessible
                if self._is_this:
                    accessible_fields = set(context.current_object_fields.keys())
                else:
                    accessible_fields = self._all_field_names

                # Validate the attribute exists in accessible fields
                if attr not in accessible_fields:
                    display_name = (
                        "'this' object" if self._is_this else f"Object '{self._name}'"
                    )
                    raise AttributeError(
                        f"{display_name} has no field '{attr}'. "
                        f"Available fields: {', '.join(sorted(accessible_fields)) if accessible_fields else 'none'}"
                    )

                # Try to resolve the field value
                if attr in self._field_definitions:
                    from snowfakery.utils.validation_utils import resolve_value

                    field_def = self._field_definitions[attr]
                    try:
                        # Track error count before resolution to detect new errors
                        error_count_before = len(context.errors)
                        resolved = resolve_value(field_def, context)
                        # If resolution added errors (e.g., from context mismatch), remove them
                        # and fall back to mock value - these aren't real errors
                        if len(context.errors) > error_count_before:
                            # Remove errors added during this resolution attempt
                            context.errors = context.errors[:error_count_before]
                            return f"<mock_{self._name}.{attr}>"
                        if resolved is not None:
                            return resolved
                    except Exception:
                        # Fall back to mock value if resolution fails
                        pass

                # Fall back to mock value if we can't resolve
                return f"<mock_{self._name}.{attr}>"

        return MockObjectRow(obj_template, name)

    def _create_this_mock(self):
        """Create mock 'this' object for the current object being created."""
        return self._create_mock_object("this")

    def _create_validation_function(self, func_name, validator):
        """Create wrapper that validates when called from Jinja.

        Args:
            func_name: Name of the function
            validator: Validator function to call

        Returns:
            Wrapper function that validates and returns mock value
        """

        def validation_wrapper(*args, **kwargs):
            # Create synthetic StructuredValue
            # Use current_field_line_num if available (for inline Jinja calls), else use template line_num
            line_num = (
                self.current_field_line_num
                if self.current_field_line_num is not None
                else (self.current_template.line_num if self.current_template else 0)
            )
            sv = StructuredValue(
                func_name,
                list(args),
                self.current_template.filename
                if self.current_template
                else "<unknown>",
                line_num,
            )
            if kwargs:
                sv.kwargs = dict(kwargs)

            # Call validator and return its mock result
            try:
                return validator(sv, self)
            except Exception as exc:
                self.add_error(
                    f"Function '{func_name}' validation failed: {exc}",
                    sv.filename,
                    sv.line_num,
                )
                return f"<result_of_{func_name}>"

        return validation_wrapper

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

                    # Create wrapper that calls validator and returns mock
                    def wrapper(*args, **kwargs):
                        # Use current_field_line_num if available (for inline Jinja calls), else use template line_num
                        line_num = (
                            self._context.current_field_line_num
                            if self._context.current_field_line_num is not None
                            else (
                                self._context.current_template.line_num
                                if self._context.current_template
                                else 0
                            )
                        )
                        sv = StructuredValue(
                            func_full_name,
                            kwargs if kwargs else list(args),
                            self._context.current_template.filename
                            if self._context.current_template
                            else "<unknown>",
                            line_num,
                        )

                        return validator(sv, self._context)

                    return wrapper
                else:
                    # No validator, return generic mock function
                    return lambda *args, **kwargs: f"<mock_{func_full_name}>"

        return MockPlugin(plugin_name, plugin_funcs, self)

    def _create_mock_faker(self):
        """Create mock Faker that validates provider names immediately.

        Returns:
            MockFaker instance that validates on attribute access
        """

        class MockFaker:
            def __init__(self, context):
                self.context = context

            def __getattr__(self, provider_name):
                # Get line number for error reporting
                line_num = (
                    self.context.current_field_line_num
                    if self.context.current_field_line_num is not None
                    else (
                        self.context.current_template.line_num
                        if self.context.current_template
                        else None
                    )
                )

                # Create StructuredValue for validate_fake (which validates provider name immediately)
                sv = StructuredValue(
                    "fake",
                    [provider_name],  # Just provider name, no args yet
                    self.context.current_template.filename
                    if self.context.current_template
                    else "<unknown>",
                    line_num,
                )

                # validate_fake returns a method - it validates the provider name immediately
                validated_method = FakerValidators.validate_fake(sv, self.context)

                # Wrap in StringGenerator for Jinja compatibility
                return StringGenerator(validated_method)

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
    base_faker = Faker()

    # Add custom providers to the faker instance
    for provider in interpreter.faker_providers:
        base_faker.add_provider(provider)

    # Create a mock faker_context for FakeNames methods that need local_vars()
    class MockFakerContext:
        """Mock context for FakeNames during validation."""

        def local_vars(self):
            """Return empty dict (no previously generated fields during validation)."""
            return {}

    fake_names = FakeNames(base_faker, faker_context=MockFakerContext())

    # Create wrapper that combines base_faker and fake_names without circular reference
    class CombinedFaker:
        """Combines Faker and FakeNames, with FakeNames methods taking precedence."""

        def __init__(self, faker_inst, fake_names_inst):
            self._faker = faker_inst
            self._fake_names = fake_names_inst

        def __getattr__(self, name):
            # Check FakeNames first (takes precedence, like runtime)
            if hasattr(self._fake_names, name):
                return getattr(self._fake_names, name)
            # Fall back to faker
            return getattr(self._faker, name)

    faker_instance = CombinedFaker(base_faker, fake_names)

    # Store faker instance in context for execution
    context.faker_instance = faker_instance

    # Extract all callable methods from the faker instance
    faker_method_names = set()
    for name in dir(base_faker):
        if name.startswith("_"):
            continue
        try:
            attr = getattr(base_faker, name, None)
            if callable(attr):
                faker_method_names.add(name)
        except (TypeError, AttributeError):
            continue
    for name in dir(fake_names):
        if name.startswith("_"):
            continue
        try:
            attr = getattr(fake_names, name, None)
            if callable(attr):
                faker_method_names.add(name)
        except (TypeError, AttributeError):
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

    def register_to_all(obj_template):
        """Register an ObjectTemplate to all_objects/all_nicknames."""
        context.all_objects[obj_template.tablename] = obj_template
        if obj_template.nickname:
            context.all_nicknames[obj_template.nickname] = obj_template

    # First pass: Pre-register ALL objects in all_objects/all_nicknames
    # This allows forward references for reference functions
    for statement in parse_result.statements:
        _walk_nested_objects(statement, register_to_all)

    # Second pass: Sequential validation with progressive registration
    for statement in parse_result.statements:
        # Set current template for Jinja context
        context.current_template = statement

        # Validate statement
        validate_statement(statement, context)

        # Clear current template
        context.current_template = None

        # Register variables (ObjectTemplates are registered inside validate_statement)
        if isinstance(statement, VariableDefinition):
            # Register variable (order matters for variables)
            context.available_variables[statement.varname] = statement

    return ValidationResult(context.errors, context.warnings)


def _walk_nested_objects(obj, on_object_found, visited=None):
    """Walk through nested structures and call callback for each ObjectTemplate found.

    Args:
        obj: Object to walk (ObjectTemplate, StructuredValue, list, dict, etc.)
        on_object_found: Callback function(obj_template) called for each ObjectTemplate
        visited: Set of visited object IDs to prevent infinite loops
    """
    if visited is None:
        visited = set()

    if isinstance(obj, ObjectTemplate):
        obj_id = id(obj)
        if obj_id in visited:
            return
        visited.add(obj_id)

        # Call callback for this object
        on_object_found(obj)

        # Recursively walk friends and fields
        for friend in obj.friends:
            _walk_nested_objects(friend, on_object_found, visited)
        for field in obj.fields:
            if isinstance(field, FieldFactory):
                _walk_nested_objects(field.definition, on_object_found, visited)

    elif isinstance(obj, StructuredValue):
        args = getattr(obj, "args", [])
        if isinstance(args, (list, tuple)):
            for arg in args:
                _walk_nested_objects(arg, on_object_found, visited)
        elif args is not None:
            _walk_nested_objects(args, on_object_found, visited)

        kwargs = getattr(obj, "kwargs", {})
        if isinstance(kwargs, dict):
            for value in kwargs.values():
                _walk_nested_objects(value, on_object_found, visited)

    elif isinstance(obj, FieldFactory):
        _walk_nested_objects(obj.definition, on_object_found, visited)

    elif isinstance(obj, (list, tuple)):
        for item in obj:
            _walk_nested_objects(item, on_object_found, visited)

    elif isinstance(obj, dict):
        for value in obj.values():
            _walk_nested_objects(value, on_object_found, visited)


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

        # Helper to register nested objects to available registries
        def register_to_available(obj_template):
            context.available_objects[obj_template.tablename] = obj_template
            if obj_template.nickname:
                context.available_nicknames[obj_template.nickname] = obj_template

        # Validate fields sequentially (order matters within object)
        for field in statement.fields:
            if isinstance(field, FieldFactory):
                # Validate field (can reference previously defined fields in this object)
                validate_field_definition(field.definition, context)

                # Register any nested objects found in the field definition
                _walk_nested_objects(field.definition, register_to_available)

                # Register field so subsequent fields can reference it
                context.current_object_fields[field.name] = field

        # Register parent object AFTER validating fields but BEFORE validating friends
        context.available_objects[statement.tablename] = statement
        if statement.nickname:
            context.available_nicknames[statement.nickname] = statement

        # Recursively validate friends (nested ObjectTemplates)
        for friend in statement.friends:
            if isinstance(friend, ObjectTemplate):
                # Save and set current_template for nested validation
                saved_template = context.current_template
                context.current_template = friend

                # Validate the friend
                validate_statement(friend, context)

                # Restore current_template
                context.current_template = saved_template

                # Register friend in sequential registries AFTER validating
                # This ensures a friend can't random_reference itself on first instance
                context.available_objects[friend.tablename] = friend
                if friend.nickname:
                    context.available_nicknames[friend.nickname] = friend

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
        # Store the field's line number for inline function calls
        saved_line_num = context.current_field_line_num
        context.current_field_line_num = line_num

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
        finally:
            # Restore the previous line number
            context.current_field_line_num = saved_line_num
    except jinja2.exceptions.UndefinedError as e:
        # Variable or name not found
        error_msg = getattr(e, "message", str(e))

        # Simplify error messages about Mock* objects to be more user-friendly
        if error_msg and "has no attribute" in error_msg:
            match = re.search(r"has no attribute '(\w+)'", error_msg)
            if match:
                attr_name = match.group(1)
                if "MockObjectRow object" in error_msg:
                    error_msg = f"Object has no attribute '{attr_name}'"
                elif "MockPlugin object" in error_msg:
                    error_msg = f"Plugin has no attribute '{attr_name}'"

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

    Args:
        field_def: A FieldDefinition object (SimpleValue or StructuredValue)
        context: The validation context

    Returns:
        For StructuredValue: The mock result returned by the validator (or None)
        For SimpleValue: The resolved value (or None)
    """
    # Check if it's a StructuredValue (function call)
    if isinstance(field_def, StructuredValue):
        # Check if this StructuredValue has already been validated (using object id)
        sv_id = id(field_def)
        if sv_id in context._structured_value_cache:
            return context._structured_value_cache[sv_id]

        func_name = field_def.function_name
        mock_result = None

        # STEP 1: Resolve nested StructuredValues in args/kwargs BEFORE calling validator
        # This allows validators to receive mock values instead of StructuredValue objects
        resolved_args = []
        for arg in field_def.args:
            if isinstance(arg, StructuredValue):
                nested_mock = validate_field_definition(arg, context)
                resolved_args.append(nested_mock)
            else:
                resolved_args.append(arg)

        resolved_kwargs = {}
        for key, value in field_def.kwargs.items():
            if isinstance(value, StructuredValue):
                nested_mock = validate_field_definition(value, context)
                resolved_kwargs[key] = nested_mock
            else:
                resolved_kwargs[key] = value

        func_name = field_def.function_name
        lookup_func_name = func_name
        fake_provider = None
        if lookup_func_name not in context.available_functions and "." in func_name:
            base_name, method_name = func_name.split(".", 1)
            if base_name == "fake":
                lookup_func_name = "fake"
                fake_provider = method_name

        # STEP 2: Temporarily replace args/kwargs (and possibly function name) with resolved versions
        original_args = field_def.args
        original_kwargs = field_def.kwargs
        original_function_name = field_def.function_name

        if fake_provider:
            resolved_args = [fake_provider] + resolved_args
            field_def.function_name = "fake"

        field_def.args = resolved_args
        field_def.kwargs = resolved_kwargs

        try:
            # STEP 3: Look up validator and call it with resolved args/kwargs
            if lookup_func_name in context.available_functions:
                validator = context.available_functions[lookup_func_name]
                try:
                    result = validator(field_def, context)

                    # STEP 3.5: If validator returned a callable (like validate_fake does),
                    # call it with the resolved args from the StructuredValue
                    if callable(result) and lookup_func_name == "fake":
                        # For fake, args[0] is provider name, args[1:] are faker arguments
                        faker_args = resolved_args[1:] if len(resolved_args) > 1 else []
                        faker_kwargs = resolved_kwargs
                        mock_result = result(*faker_args, **faker_kwargs)
                    else:
                        mock_result = result
                except Exception as e:
                    # Catch any validator errors to avoid breaking the validation process
                    context.add_error(
                        f"Internal validation error for '{func_name}': {str(e)}",
                        getattr(field_def, "filename", None),
                        getattr(field_def, "line_num", None),
                    )
            else:
                # Check if it's a plugin function without a validator
                if "." in func_name:
                    plugin_name, method_name = func_name.split(".", 1)
                    if plugin_name in context.interpreter.plugin_instances:
                        # Plugin exists but function has no validator - return generic mock
                        mock_result = f"<result_of_{func_name}>"
                    else:
                        # Plugin doesn't exist - report error
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
        finally:
            # STEP 4: Restore original args/kwargs
            field_def.args = original_args
            field_def.kwargs = original_kwargs
            field_def.function_name = original_function_name

        # Cache the result to prevent duplicate validation
        context._structured_value_cache[sv_id] = mock_result
        return mock_result

    # Check if it's a SimpleValue (literal or Jinja template)
    elif isinstance(field_def, SimpleValue):
        if isinstance(field_def.definition, str) and "${{" in field_def.definition:
            # It's a Jinja template - validate it
            result = validate_jinja_template_by_execution(
                field_def.definition, field_def.filename, field_def.line_num, context
            )
            return result
        else:
            # Return the literal value
            return field_def.definition if hasattr(field_def, "definition") else None

    return None
