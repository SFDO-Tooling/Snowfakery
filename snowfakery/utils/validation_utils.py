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
        if isinstance(value, str) and value.startswith("<") and value.endswith(">"):
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
                            if (
                                isinstance(resolved, str)
                                and resolved.startswith("<")
                                and resolved.endswith(">")
                            ):
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
        validate_field_definition(value, context)

        # Now try to actually execute the function and return the result
        func_name = value.function_name

        # Resolve arguments (recursively resolve nested StructuredValues)
        resolved_args = []
        for arg in value.args:
            resolved_arg = resolve_value(arg, context)
            if resolved_arg is None and not isinstance(
                arg, (int, float, str, bool, type(None))
            ):
                # Could not resolve argument, can't execute function
                return None
            resolved_args.append(resolved_arg if resolved_arg is not None else arg)

        # Resolve keyword arguments
        resolved_kwargs = {}
        for key, kwarg in value.kwargs.items():
            resolved_kwarg = resolve_value(kwarg, context)
            if resolved_kwarg is None and not isinstance(
                kwarg, (int, float, str, bool, type(None))
            ):
                # Could not resolve argument, can't execute function
                return None
            resolved_kwargs[key] = (
                resolved_kwarg if resolved_kwarg is not None else kwarg
            )

        # Try to execute the actual function
        try:
            # Check standard functions
            if context.interpreter and func_name in context.interpreter.standard_funcs:
                actual_func = context.interpreter.standard_funcs[func_name]
                if callable(actual_func):
                    return actual_func(*resolved_args, **resolved_kwargs)

            # Check plugin functions
            if context.interpreter:
                for _, plugin_instance in context.interpreter.plugin_instances.items():
                    funcs = plugin_instance.custom_functions()
                    if func_name in dir(funcs):
                        actual_func = getattr(funcs, func_name)
                        if callable(actual_func):
                            return actual_func(*resolved_args, **resolved_kwargs)
        except Exception:
            # Could not execute function, return None
            pass

        return None

    return None
