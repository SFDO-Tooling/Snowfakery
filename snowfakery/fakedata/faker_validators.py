"""Validators for Faker provider calls using introspection."""

import inspect
from typing import get_origin, get_args, Union, Optional, Literal
from snowfakery.utils.validation_utils import resolve_value, get_fuzzy_match


class FakerValidators:
    """Validates Faker provider calls using introspection.

    This class uses Python's inspect module to introspect Faker method signatures
    and validate parameter names, counts, and types (when type annotations are available).
    """

    def __init__(self, faker_instance, faker_providers=None):
        """Initialize validator with Faker instance.

        Args:
            faker_instance: The Faker instance to introspect
            faker_providers: Set of available provider names (optional, extracted from faker_instance if not provided)
        """
        self.faker_instance = faker_instance
        self.faker_providers = faker_providers or self._extract_providers()
        self._signature_cache = {}  # Cache signatures for performance

    def _extract_providers(self):
        """Extract provider names from faker instance."""
        if not self.faker_instance:
            return set()

        providers = set()
        skip_attrs = {
            "seed",
            "seed_instance",
            "seed_locale",
        }  # Methods that raise errors
        for name in dir(self.faker_instance):
            if not name.startswith("_") and name not in skip_attrs:
                try:
                    attr = getattr(self.faker_instance, name)
                    if callable(attr):
                        providers.add(name)
                except (TypeError, AttributeError):
                    # Skip attributes that raise errors on access
                    pass
        return providers

    def _resolve_provider_name(self, provider_name: str) -> Optional[str]:
        """Resolve provider name accounting for case and underscores."""
        if not provider_name:
            return None
        if provider_name in self.faker_providers:
            return provider_name

        normalized = provider_name.replace("_", "").lower()
        for candidate in self.faker_providers:
            if candidate.lower() == provider_name.lower():
                return candidate
            if candidate.replace("_", "").lower() == normalized:
                return candidate
        return None

    def validate_provider_name(
        self, provider_name, context, filename=None, line_num=None
    ):
        """Validate that a provider name exists.

        Args:
            provider_name: Name of the Faker provider
            context: ValidationContext for error reporting
            filename: Source filename for error reporting
            line_num: Line number for error reporting

        Returns:
            Resolved provider name string if provider exists, otherwise None
        """
        resolved_name = self._resolve_provider_name(provider_name)
        if not resolved_name:
            suggestion = get_fuzzy_match(provider_name, list(self.faker_providers))
            msg = f"Unknown Faker provider '{provider_name}'"
            if suggestion:
                msg += f". Did you mean '{suggestion}'?"
            context.add_error(msg, filename, line_num)
            return None
        return resolved_name

    def validate_provider_call(self, provider_name, args, kwargs, context):
        """Validate a Faker provider call.

        This method validates:
        - Parameter names (catches typos)
        - Parameter counts (too many/few arguments)
        - Parameter types (when type annotations available)

        Args:
            provider_name: Name of the Faker provider (e.g., "email", "first_name")
            args: Positional arguments (list)
            kwargs: Keyword arguments (dict)
            context: ValidationContext for error reporting
        """
        resolved_name: Optional[str] = self._resolve_provider_name(provider_name)
        if not resolved_name:
            # Re-use name validation to record a helpful error message
            self.validate_provider_name(provider_name, context)
            return

        # 1. Check if provider exists
        if not hasattr(self.faker_instance, resolved_name):
            return

        # 2. Get the method
        method = getattr(self.faker_instance, resolved_name)

        # 3. Get signature (with caching)
        if resolved_name not in self._signature_cache:
            try:
                sig = inspect.signature(method)
                self._signature_cache[resolved_name] = sig
            except (ValueError, TypeError):
                # Can't introspect (rare case) - skip validation
                return

        sig = self._signature_cache[resolved_name]

        # 4. Resolve arguments (convert FieldDefinitions to actual values)
        resolved_args = []
        for arg in args:
            resolved = resolve_value(arg, context)
            # Use resolved value if available, otherwise use original
            resolved_args.append(resolved if resolved is not None else arg)

        resolved_kwargs = {}
        for key, value in kwargs.items():
            resolved = resolve_value(value, context)
            resolved_kwargs[key] = resolved if resolved is not None else value

        # 5. Validate parameter names and counts using sig.bind()
        try:
            bound = sig.bind(*resolved_args, **resolved_kwargs)
        except TypeError as e:
            # Parameter validation failed (wrong names, counts, etc.)
            filename = (
                context.current_template.filename if context.current_template else None
            )
            line_num = (
                context.current_template.line_num if context.current_template else None
            )
            context.add_error(
                f"fake.{provider_name}: {str(e)}",
                filename,
                line_num,
            )
            return

        # 6. Type checking (if parameters have type annotations)
        explicitly_provided = set(bound.arguments.keys())
        bound.apply_defaults()
        for param_name, param_value in bound.arguments.items():
            param_obj = sig.parameters[param_name]

            # Skip if no annotation
            if param_obj.annotation == inspect.Parameter.empty:
                continue

            # Skip type checking for default values - only check explicitly provided args
            if param_name not in explicitly_provided:
                continue

            # Only validate if we have a resolved literal value
            if not isinstance(param_value, (int, float, str, bool, type(None))):
                # Can't validate non-literal values (complex expressions)
                continue

            # Check type compatibility
            expected_type = param_obj.annotation
            if not self._check_type(param_value, expected_type):
                # Type mismatch - report error
                filename = (
                    context.current_template.filename
                    if context.current_template
                    else None
                )
                line_num = (
                    context.current_template.line_num
                    if context.current_template
                    else None
                )

                context.add_error(
                    f"fake.{provider_name}: Parameter '{param_name}' "
                    f"expects {self._format_type(expected_type)}, "
                    f"got {type(param_value).__name__}",
                    filename,
                    line_num,
                )

    def _check_type(self, value, expected_type):
        """Check if value matches expected type annotation.

        Handles:
        - Simple types (bool, int, str, float)
        - Optional[T] (Union[T, None])
        - Union[T1, T2, ...]
        - Literal[value1, value2, ...]

        Args:
            value: The value to check
            expected_type: The type annotation from signature

        Returns:
            True if type matches, False otherwise
        """
        # Handle None - only accept if type explicitly includes NoneType
        if value is None:
            origin = get_origin(expected_type)
            if origin is Union:
                args = get_args(expected_type)
                return type(None) in args
            return False

        # Handle Literal types (e.g., Literal[False], Literal["a", "b"])
        origin = get_origin(expected_type)
        if origin is Literal:
            literal_values = get_args(expected_type)
            return value in literal_values

        # Handle Union types (e.g., Union[str, int], Optional[str])
        if origin is Union:
            args = get_args(expected_type)
            # Check if value matches any of the union types
            for arg in args:
                if arg is type(None):
                    continue  # Skip NoneType
                # Recursively check each union member (handles nested Literal)
                if self._check_type(value, arg):
                    return True
            return False

        # Simple type check
        try:
            if isinstance(expected_type, type):
                return isinstance(value, expected_type)
        except TypeError:
            # Complex type annotation we can't check
            pass

        # Can't validate complex annotations, assume valid
        return True

    def _format_type(self, type_annotation):
        """Format type annotation for error messages.

        Converts type annotations to human-readable strings:
        - bool → "bool"
        - Optional[str] → "str or None"
        - Union[int, str] → "int or str"
        - Literal[False] → "False"
        - Literal["a", "b"] → "'a' or 'b'"

        Args:
            type_annotation: The type annotation to format

        Returns:
            Human-readable type string
        """
        origin = get_origin(type_annotation)

        # Handle Literal types
        if origin is Literal:
            literal_values = get_args(type_annotation)
            if len(literal_values) == 1:
                val = literal_values[0]
                return repr(val) if isinstance(val, str) else str(val)
            return " or ".join(
                repr(v) if isinstance(v, str) else str(v) for v in literal_values
            )

        if origin is Union:
            args = get_args(type_annotation)
            # Filter out NoneType for cleaner messages
            non_none = [arg for arg in args if arg is not type(None)]

            if len(non_none) == 1:
                # Optional[T] case - show as "T or None"
                if type(None) in args:
                    formatted = self._format_type(non_none[0])
                    return f"{formatted} or None"
                return self._format_type(non_none[0])

            # Union case - show all types
            type_names = []
            for arg in args:
                if arg is type(None):
                    type_names.append("None")
                else:
                    type_names.append(self._format_type(arg))
            return " or ".join(type_names)

        # Simple type
        if hasattr(type_annotation, "__name__"):
            return type_annotation.__name__

        # Fallback to string representation
        return str(type_annotation)

    @staticmethod
    def validate_fake(sv, context):
        """Validate fake StructuredValue calls and return a callable method.

        This is the validator for the StructuredValue syntax:
            fake: provider_name
        or with parameters:
            fake:
              - provider_name
              - param1
              - param2

        Args:
            sv: StructuredValue with function_name="fake"
            context: ValidationContext for error reporting

        Returns:
            A callable method that validates and executes Faker when called.
            The caller is responsible for calling the method (with args from sv if needed).
        """
        # Get provider name from first arg
        args = getattr(sv, "args", [])
        if not args:
            context.add_error(
                "fake: Missing provider name",
                getattr(sv, "filename", None),
                getattr(sv, "line_num", None),
            )
            return lambda *a, **kw: None

        provider_name = resolve_value(args[0], context)
        if not provider_name or not isinstance(provider_name, str):
            # Could not resolve provider name to a string
            return lambda *a, **kw: None

        # Check if Faker instance available
        if not context.faker_instance:
            # No Faker instance available - return None
            return lambda *a, **kw: None

        # Use FakerValidators to validate provider name
        validator = FakerValidators(context.faker_instance, context.faker_providers)

        # Validate provider name immediately
        resolved_name = validator.validate_provider_name(
            provider_name,
            context,
            getattr(sv, "filename", None),
            getattr(sv, "line_num", None),
        )

        if not resolved_name:
            # Validation failed, return mock placeholder
            return lambda *a, **kw: f"<fake_{provider_name}>"

        # Return a method that validates parameters and executes when called
        def validated_faker_method(*call_args, **call_kwargs):
            """Execute Faker method with parameter validation."""
            # Resolve parameters before validation and execution
            resolved_args = []
            for arg in call_args:
                resolved = resolve_value(arg, context)
                # Use resolved value if available, otherwise use original
                resolved_args.append(resolved if resolved is not None else arg)

            resolved_kwargs = {}
            for key, value in call_kwargs.items():
                resolved = resolve_value(value, context)
                resolved_kwargs[key] = resolved if resolved is not None else value

            # Validate parameters when method is called
            if resolved_args or resolved_kwargs:
                error_count_before = len(context.errors)
                validator.validate_provider_call(
                    resolved_name, resolved_args, resolved_kwargs, context
                )
                if len(context.errors) > error_count_before:
                    return f"<fake_{provider_name}>"

            # Execute Faker method with RESOLVED parameters
            try:
                method = getattr(context.faker_instance, resolved_name)
                return method(*resolved_args, **resolved_kwargs)
            except Exception as e:
                context.add_error(
                    f"fake.{resolved_name}: Execution error: {str(e)}",
                    getattr(sv, "filename", None),
                    getattr(sv, "line_num", None),
                )
                return f"<fake_{provider_name}>"

        return validated_faker_method
