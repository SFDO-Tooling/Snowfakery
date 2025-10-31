"""Utility functions for recipe validation."""

import difflib
from typing import List, Optional


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


def resolve_value(value, context):
    """Try to resolve a value to a literal.

    This attempts simple resolution of values:
    - If it's already a literal (int, float, str, bool, None): return as-is
    - If it's a SimpleValue with a literal: extract and return it
    - If it's a variable reference: look it up in context
    - Otherwise: return None (cannot resolve statically)

    Args:
        value: The value to resolve (can be FieldDefinition or literal)
        context: ValidationContext with variable registry

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
        return value

    # SimpleValue - might be a literal or variable reference
    if isinstance(value, SimpleValue):
        # Check if it's a pure literal (no Jinja template)
        if hasattr(value, "definition"):
            raw_value = value.definition
            if isinstance(raw_value, (int, float, str, bool, type(None))):
                return raw_value

        # TODO: For full implementation, parse Jinja expressions here
        return None

    # StructuredValue - cannot resolve statically, but should be validated recursively
    if isinstance(value, StructuredValue):
        return None

    return None
