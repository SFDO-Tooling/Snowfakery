"""Utility functions for recipe validation."""

import difflib
from typing import List, Optional, Any
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


def resolve_value(value, context):
    """Try to resolve a value to a literal by executing Jinja if needed.

    This attempts resolution of values:
    - If it's already a literal (int, float, str, bool, None): return as-is (unless it's a mock placeholder)
    - If it's a SimpleValue with a literal: extract and return it
    - If it's a SimpleValue with Jinja: execute Jinja and return resolved value
    - If it's a StructuredValue: validate and return mock result from validator
    - Mock placeholder strings (e.g., "<mock_*>") are filtered out and return None
    - Otherwise: return None (cannot resolve)

    Args:
        value: The value to resolve (can be FieldDefinition or literal)
        context: ValidationContext with interpreter for Jinja execution

    Returns:
        The resolved literal value, or None if cannot be resolved or is a mock placeholder
    """
    # Import here to avoid circular import
    from snowfakery.data_generator_runtime_object_model import (
        SimpleValue,
        StructuredValue,
    )
    from snowfakery.recipe_validator import validate_field_definition

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

    # StructuredValue - validate and return mock result
    if isinstance(value, StructuredValue):
        # Validate the StructuredValue and get the mock result from the validator
        mock_result = validate_field_definition(value, context)

        # Check if result is a mock placeholder string
        if is_mock_value(mock_result):
            # Don't pass mock placeholders as literals
            return None

        return mock_result

    return None
