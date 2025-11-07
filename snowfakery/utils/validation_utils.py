"""Utility functions for recipe validation."""

import difflib
from typing import List, Optional, Any, Callable
from contextlib import contextmanager

# Constants for mock value detection
MOCK_VALUE_PREFIX = "<mock_"
MOCK_VALUE_SUFFIX = ">"


class MockRuntimeContext:
    """Mock runtime context for validation.

    This provides the field_vars() and context_vars() methods that plugin functions
    need during validation. It can be used with either a ValidationContext or a
    pre-built namespace dict.
    """

    def __init__(self, validation_context: Any, namespace: Optional[dict] = None):
        """Initialize mock context.

        Args:
            validation_context: The ValidationContext instance
            namespace: Optional pre-built namespace dict. If not provided,
                      will call validation_context.field_vars() when needed.
        """
        self._validation_context = validation_context
        self._namespace = namespace
        # Attributes needed by @memorable decorator
        self.recalculate_every_time = False
        self.unique_context_identifier = "validation_context"

    def field_vars(self):
        """Return the validation namespace."""
        if self._namespace is not None:
            # Use pre-built namespace (for Jinja execution)
            return self._namespace
        else:
            # Build namespace on demand (for StructuredValue execution)
            return self._validation_context.field_vars()

    def context_vars(self, plugin_namespace):
        """Return empty context vars for validation."""
        return {}


@contextmanager
def with_mock_context(validation_context: Any, namespace: Optional[dict] = None):
    """Context manager to temporarily set up mock runtime context.

    Args:
        validation_context: The ValidationContext instance
        namespace: Optional pre-built namespace dict

    Yields:
        The MockRuntimeContext instance
    """
    interpreter = validation_context.interpreter
    saved_context = getattr(interpreter, "current_context", None)

    mock_context = MockRuntimeContext(validation_context, namespace)
    interpreter.current_context = mock_context

    try:
        yield mock_context
    finally:
        interpreter.current_context = saved_context


def get_fuzzy_match(
    name: str, available_names: List[str], cutoff: float = 0.6
) -> Optional[str]:
    """Find the closest match for a name using fuzzy matching.

    Args:
        name: The name to find a match for
        available_names: List of valid names to match against
        cutoff: Minimum similarity ratio (0.0 to 1.0)

    Returns:
        The closest matching name, or None if no good match found
    """
    if not available_names:
        return None

    matches = difflib.get_close_matches(name, available_names, n=1, cutoff=cutoff)
    return matches[0] if matches else None


def is_mock_value(value: Any) -> bool:
    """Check if value is a validation mock placeholder.

    Mock values are string placeholders generated during validation that
    start with "<mock_" and end with ">". These should not be treated as
    real values for type checking or resolution.

    Args:
        value: The value to check

    Returns:
        True if value is a mock placeholder, False otherwise
    """
    return (
        isinstance(value, str)
        and value.startswith(MOCK_VALUE_PREFIX)
        and value.endswith(MOCK_VALUE_SUFFIX)
    )


def validate_and_check_errors(context: Any, validator_fn: Callable, *args) -> bool:
    """Execute validator and check if errors were added.

    This helper tracks the error count before and after validation to determine
    if the validator added any errors. This is useful for conditional logic that
    depends on validation results.

    Args:
        context: ValidationContext instance
        validator_fn: Validator function to call
        *args: Arguments to pass to validator function

    Returns:
        True if validator added errors, False otherwise
    """
    errors_before = len(context.errors)
    validator_fn(*args)
    errors_after = len(context.errors)
    return errors_after > errors_before


def resolve_value(value, context):
    """Try to resolve a value to a literal by executing Jinja if needed.

    This attempts resolution of values:
    - If it's already a literal (int, float, str, bool, None): return as-is
    - If it's a SimpleValue with a literal: extract and return it
    - If it's a SimpleValue with Jinja: execute Jinja and return resolved value
    - Otherwise: return None (cannot resolve)

    Args:
        value: The value to resolve (can be FieldDefinition or literal)
        context: ValidationContext with interpreter for Jinja execution

    Returns:
        The resolved literal value, or None if cannot be resolved
    """
    # Import here to avoid circular import
    from snowfakery.data_generator_runtime_object_model import (
        SimpleValue,
        StructuredValue,
    )

    # Already a literal
    if isinstance(value, (int, float, str, bool, type(None))):
        # Check if it's a mock value (validation placeholder)
        if is_mock_value(value):
            # Mock value - cannot resolve, return None so validators skip type checks
            return None
        return value

    # SimpleValue - might be a literal or Jinja template
    if isinstance(value, SimpleValue):
        if hasattr(value, "definition"):
            raw_value = value.definition

            # Pure literal (no Jinja)
            if isinstance(raw_value, (int, float, bool, type(None))):
                return raw_value

            # String - check if it contains Jinja
            if isinstance(raw_value, str):
                if "${{" in raw_value or "${%" in raw_value:
                    # Contains Jinja - execute it to resolve
                    if context.interpreter and context.current_template:
                        from snowfakery.recipe_validator import (
                            validate_jinja_template_by_execution,
                        )

                        resolved = validate_jinja_template_by_execution(
                            raw_value, value.filename, value.line_num, context
                        )

                        # Return resolved value if it's a literal
                        if isinstance(resolved, (int, float, str, bool, type(None))):
                            # Check if it's a mock value (validation placeholder)
                            if is_mock_value(resolved):
                                # Mock value - cannot resolve
                                return None
                            return resolved
                else:
                    # No Jinja, just a literal string
                    return raw_value

    # StructuredValue - execute it by validating and calling the function
    if isinstance(value, StructuredValue):
        from snowfakery.recipe_validator import validate_field_definition

        # Validate the StructuredValue (this also executes it via validation wrapper)
        # If validation added errors, don't attempt execution
        if validate_and_check_errors(
            context, validate_field_definition, value, context
        ):
            return None

        # Now try to actually execute the function and return the result
        func_name = value.function_name

        # Resolve arguments (recursively resolve nested StructuredValues)
        resolved_args = []
        for arg in value.args:
            resolved_arg = resolve_value(arg, context)
            if resolved_arg is None and not isinstance(
                arg, (int, float, str, bool, type(None))
            ):
                # Check if it's a SimpleValue wrapping None - that's OK
                if (
                    isinstance(arg, SimpleValue)
                    and hasattr(arg, "definition")
                    and arg.definition is None
                ):
                    # SimpleValue(None) is valid, resolved correctly to None
                    resolved_args.append(None)
                    continue
                # Could not resolve a complex argument, can't execute function
                return None
            resolved_args.append(resolved_arg if resolved_arg is not None else arg)

        # Resolve keyword arguments
        resolved_kwargs = {}
        for key, kwarg in value.kwargs.items():
            resolved_kwarg = resolve_value(kwarg, context)
            if resolved_kwarg is None and not isinstance(
                kwarg, (int, float, str, bool, type(None))
            ):
                # Check if it's a SimpleValue wrapping None - that's OK
                if (
                    isinstance(kwarg, SimpleValue)
                    and hasattr(kwarg, "definition")
                    and kwarg.definition is None
                ):
                    # SimpleValue(None) is valid, resolved correctly to None
                    resolved_kwargs[key] = None
                    continue
                # Could not resolve a complex argument, can't execute function
                return None
            resolved_kwargs[key] = (
                resolved_kwarg if resolved_kwarg is not None else kwarg
            )

        # Try to execute the actual function
        try:
            # Check for Faker provider (special case: fake: provider_name)
            if func_name == "fake" and context.faker_instance and resolved_args:
                # First argument should be the provider name
                provider_name = resolved_args[0]
                if isinstance(provider_name, str) and hasattr(
                    context.faker_instance, provider_name
                ):
                    faker_method = getattr(context.faker_instance, provider_name)
                    if callable(faker_method):
                        # Call with remaining args and kwargs
                        faker_args = resolved_args[1:] if len(resolved_args) > 1 else []
                        return faker_method(*faker_args, **resolved_kwargs)

            # Check standard functions
            if context.interpreter and func_name in context.interpreter.standard_funcs:
                actual_func = context.interpreter.standard_funcs[func_name]
                if callable(actual_func):
                    return actual_func(*resolved_args, **resolved_kwargs)

            # Check plugin functions (handle plugin namespace: "PluginName.method_name")
            if context.interpreter and "." in func_name:
                plugin_name, method_name = func_name.split(".", 1)
                if plugin_name in context.interpreter.plugin_instances:
                    plugin_instance = context.interpreter.plugin_instances[plugin_name]

                    # Set up mock context for plugin function execution
                    with with_mock_context(context):
                        funcs = plugin_instance.custom_functions()
                        if hasattr(funcs, method_name):
                            actual_func = getattr(funcs, method_name)
                            if callable(actual_func):
                                result = actual_func(*resolved_args, **resolved_kwargs)
                                return result
        except Exception:
            # Could not execute function, return None
            pass

        return None

    return None
