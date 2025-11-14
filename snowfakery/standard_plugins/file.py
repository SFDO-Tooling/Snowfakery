from pathlib import Path

from snowfakery.plugins import SnowfakeryPlugin
from snowfakery.utils.validation_utils import resolve_value


class File(SnowfakeryPlugin):
    class Functions:
        def file_data(self, file, encoding="utf-8"):
            if encoding == "binary":
                encoding = "latin-1"

            template_path = Path(self.context.current_filename).parent

            with open(template_path / file, "rb") as data:
                return data.read().decode(encoding)

    class Validators:
        """Validators for File plugin functions."""

        @staticmethod
        def validate_file_data(sv, context):
            """Validate File.file_data(file, encoding="utf-8")

            Args:
                sv: StructuredValue with args/kwargs
                context: ValidationContext for error reporting

            Returns:
                str: Mock file content or actual file content if file exists
            """
            kwargs = getattr(sv, "kwargs", {})
            args = getattr(sv, "args", [])

            # Check if file is provided (as positional or keyword argument)
            has_file = len(args) > 0 or "file" in kwargs

            if not has_file:
                context.add_error(
                    "File.file_data: Missing required parameter 'file'",
                    getattr(sv, "filename", None),
                    getattr(sv, "line_num", None),
                )
                return "Mock file content"  # Fallback mock

            # Validate file parameter
            if args:
                file_val = resolve_value(args[0], context)
            else:
                file_val = resolve_value(kwargs.get("file"), context)

            if file_val is not None:
                # ERROR: Must be string
                if not isinstance(file_val, str):
                    context.add_error(
                        f"File.file_data: 'file' must be a string, got {type(file_val).__name__}",
                        getattr(sv, "filename", None),
                        getattr(sv, "line_num", None),
                    )
                else:
                    # ERROR: File must exist
                    # Get the recipe file's directory
                    if context.current_template and context.current_template.filename:
                        template_path = Path(context.current_template.filename).parent
                        file_path = template_path / file_val

                        if not file_path.exists():
                            context.add_error(
                                f"File.file_data: File '{file_val}' does not exist (resolved to: {file_path})",
                                getattr(sv, "filename", None),
                                getattr(sv, "line_num", None),
                            )
                        elif not file_path.is_file():
                            context.add_error(
                                f"File.file_data: Path '{file_val}' exists but is not a file (resolved to: {file_path})",
                                getattr(sv, "filename", None),
                                getattr(sv, "line_num", None),
                            )

            # Validate encoding parameter (optional)
            if "encoding" in kwargs:
                encoding_val = resolve_value(kwargs["encoding"], context)

                if encoding_val is not None:
                    # ERROR: Must be string
                    if not isinstance(encoding_val, str):
                        context.add_error(
                            f"File.file_data: 'encoding' must be a string, got {type(encoding_val).__name__}",
                            getattr(sv, "filename", None),
                            getattr(sv, "line_num", None),
                        )

            # WARNING: Unknown parameters
            valid_params = {"file", "encoding"}
            unknown = set(kwargs.keys()) - valid_params
            if unknown:
                context.add_warning(
                    f"File.file_data: Unknown parameter(s): {', '.join(sorted(unknown))}",
                    getattr(sv, "filename", None),
                    getattr(sv, "line_num", None),
                )

            # Return intelligent mock: mock file content string
            return "Mock file content"
