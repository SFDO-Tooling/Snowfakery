from base64 import b64encode
from snowfakery.plugins import SnowfakeryPlugin
from snowfakery.utils.validation_utils import resolve_value


class Base64(SnowfakeryPlugin):
    class Functions:
        def encode(self, data):
            return b64encode(bytes(str(data), "latin1")).decode("ascii")

    class Validators:
        """Validators for Base64 plugin functions."""

        @staticmethod
        def validate_encode(sv, context):
            """Validate Base64.encode(data)

            Args:
                sv: StructuredValue with args/kwargs
                context: ValidationContext for error reporting

            Returns:
                str: Base64-encoded mock data
            """

            kwargs = getattr(sv, "kwargs", {})
            args = getattr(sv, "args", [])

            # Check if data is provided (as positional or keyword argument)
            has_data = len(args) > 0 or "data" in kwargs

            if not has_data:
                context.add_error(
                    "Base64.encode: Missing required parameter 'data'",
                    getattr(sv, "filename", None),
                    getattr(sv, "line_num", None),
                )
                return b64encode(b"Mock data").decode("ascii")  # Fallback

            # WARNING: Unknown parameters (only 'data' is valid)
            valid_params = {"data"}
            unknown = set(kwargs.keys()) - valid_params
            if unknown:
                context.add_warning(
                    f"Base64.encode: Unknown parameter(s): {', '.join(sorted(unknown))}",
                    getattr(sv, "filename", None),
                    getattr(sv, "line_num", None),
                )

            # Try to resolve and encode the data
            data_val = args[0] if args else kwargs.get("data")
            resolved_data = resolve_value(data_val, context)

            if resolved_data is not None:
                try:
                    # Encode the resolved data
                    return b64encode(bytes(str(resolved_data), "latin1")).decode(
                        "ascii"
                    )
                except Exception:
                    pass

            return b64encode(b"Mock data").decode("ascii")  # Fallback
