import math

from snowfakery.plugins import SnowfakeryPlugin
from snowfakery.utils.validation_utils import get_fuzzy_match, resolve_value


class Math(SnowfakeryPlugin):
    def custom_functions(self, *args, **kwargs):
        "Expose math functions to Snowfakery"

        class MathNamespace:
            pass

        mathns = MathNamespace()
        mathns.__dict__ = math.__dict__.copy()

        mathns.pi = math.pi
        mathns.round = round
        mathns.min = min
        mathns.max = max

        return mathns

    class Validators:
        """Validators for Math plugin - validates function name existence only."""

        # Class-level cache of valid names (built once at class definition time)
        _valid_names = set(name for name in dir(math) if not name.startswith("_")) | {
            "round",
            "min",
            "max",
        }

        @staticmethod
        def _validate_math_function(sv, context, expected_func_name):
            """Generic validator for any Math.* function call.

            This validator checks that the function/constant name exists,
            then tries to execute it with resolved parameters.

            Args:
                sv: StructuredValue with function call
                context: ValidationContext for error reporting
                expected_func_name: The expected function name (e.g., "sqrt")

            Returns:
                float: Result of executing the function, or 1.0 as fallback
            """

            func_name = sv.function_name

            # Extract method name from "Math.sqrt" -> "sqrt"
            if "." in func_name:
                _, method_name = func_name.split(".", 1)
            else:
                method_name = func_name

            # Check if method exists (use cached valid_names)
            if method_name not in Math.Validators._valid_names:
                suggestion = get_fuzzy_match(
                    method_name, list(Math.Validators._valid_names)
                )

                msg = f"Math.{method_name}: Unknown function or constant"
                if suggestion:
                    msg += f". Did you mean 'Math.{suggestion}'?"

                context.add_error(
                    msg,
                    getattr(sv, "filename", None),
                    getattr(sv, "line_num", None),
                )
                return 1.0  # Fallback mock

            # Try to execute the function with resolved args
            try:
                # Get the function object
                func_attr = getattr(math, method_name, None)
                if func_attr is None:
                    # Built-in like round, min, max
                    func_attr = {"round": round, "min": min, "max": max}.get(
                        method_name
                    )

                if func_attr and callable(func_attr):
                    # Resolve args
                    args = getattr(sv, "args", [])
                    resolved_args = [resolve_value(arg, context) for arg in args]

                    # Execute if all args resolved to non-None values
                    if resolved_args and all(arg is not None for arg in resolved_args):
                        result = func_attr(*resolved_args)
                        return (
                            float(result)
                            if not isinstance(result, (list, tuple))
                            else result
                        )
            except Exception:
                # Execution failed, fall through to fallback
                pass

            # Fallback mock for constants or when execution fails
            return 1.0


# Only create validators for callable functions, not constants (like pi, e, tau)
for _func_name in Math.Validators._valid_names:
    # Check if it's a callable function (not a constant like pi, e, tau)
    _attr = getattr(math, _func_name, None)
    if _attr is None:
        # Built-in like round, min, max
        _attr = {"round": round, "min": min, "max": max}.get(_func_name)

    # Only create validator for callable functions, skip constants
    if callable(_attr):

        def _make_validator(fn):
            @staticmethod
            def validator(sv, context):
                return Math.Validators._validate_math_function(sv, context, fn)

            return validator

        setattr(Math.Validators, f"validate_{_func_name}", _make_validator(_func_name))
