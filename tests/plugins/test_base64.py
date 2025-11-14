from base64 import b64encode
from io import StringIO

from snowfakery.api import generate_data
from snowfakery.data_generator_runtime_object_model import StructuredValue
from snowfakery.recipe_validator import ValidationContext
from snowfakery.standard_plugins.base64 import Base64


def expected_base64(data):
    """Helper to compute expected base64 encoding (matches plugin implementation)."""
    return b64encode(bytes(str(data), "latin1")).decode("ascii")


class TestBase64Functions:
    """Test Base64 plugin runtime functionality."""

    def test_encode_basic(self, generated_rows):
        """Test basic encoding"""
        yaml = """
            - plugin: snowfakery.standard_plugins.base64.Base64
            - object: Example
              fields:
                encoded:
                  Base64.encode: Hello World
        """
        generate_data(StringIO(yaml))
        encoded = generated_rows.row_values(0, "encoded")
        assert encoded == expected_base64("Hello World")

    def test_encode_with_keyword_arg(self, generated_rows):
        """Test encoding with keyword argument"""
        yaml = """
            - plugin: snowfakery.standard_plugins.base64.Base64
            - object: Example
              fields:
                encoded:
                  Base64.encode:
                    data: Test Data
        """
        generate_data(StringIO(yaml))
        encoded = generated_rows.row_values(0, "encoded")
        assert encoded == expected_base64("Test Data")

    def test_encode_with_variable(self, generated_rows):
        """Test encoding with variable reference"""
        yaml = """
            - plugin: snowfakery.standard_plugins.base64.Base64
            - var: my_data
              value: Some Text
            - object: Example
              fields:
                encoded:
                  Base64.encode: ${{my_data}}
        """
        generate_data(StringIO(yaml))
        encoded = generated_rows.row_values(0, "encoded")
        assert encoded == expected_base64("Some Text")

    def test_encode_numeric(self, generated_rows):
        """Test encoding numeric data (converted to string)"""
        yaml = """
            - plugin: snowfakery.standard_plugins.base64.Base64
            - object: Example
              fields:
                encoded:
                  Base64.encode: 12345
        """
        generate_data(StringIO(yaml))
        encoded = generated_rows.row_values(0, "encoded")
        assert encoded == expected_base64(12345)


class TestBase64Validator:
    """Test validators for Base64.encode()"""

    def test_valid_positional_arg(self):
        """Test valid call with positional argument"""
        context = ValidationContext()
        sv = StructuredValue("Base64.encode", ["Hello"], "test.yml", 10)

        Base64.Validators.validate_encode(sv, context)

        assert len(context.errors) == 0
        assert len(context.warnings) == 0

    def test_valid_keyword_arg(self):
        """Test valid call with keyword argument"""
        context = ValidationContext()
        sv = StructuredValue("Base64.encode", {"data": "Hello"}, "test.yml", 10)

        Base64.Validators.validate_encode(sv, context)

        assert len(context.errors) == 0
        assert len(context.warnings) == 0

    def test_missing_data_parameter(self):
        """Test error when data parameter is missing"""
        context = ValidationContext()
        sv = StructuredValue("Base64.encode", {}, "test.yml", 10)

        Base64.Validators.validate_encode(sv, context)

        assert len(context.errors) >= 1
        assert any(
            "missing required parameter" in err.message.lower()
            and "data" in err.message.lower()
            for err in context.errors
        )

    def test_unknown_parameter(self):
        """Test warning for unknown parameters"""
        context = ValidationContext()
        sv = StructuredValue(
            "Base64.encode",
            {"data": "Hello", "encoding": "utf-8"},  # 'encoding' is not valid
            "test.yml",
            10,
        )

        Base64.Validators.validate_encode(sv, context)

        assert len(context.errors) == 0
        assert len(context.warnings) >= 1
        assert any(
            "unknown parameter" in warn.message.lower()
            and "encoding" in warn.message.lower()
            for warn in context.warnings
        )

    def test_multiple_unknown_parameters(self):
        """Test warning for multiple unknown parameters"""
        context = ValidationContext()
        sv = StructuredValue(
            "Base64.encode",
            {
                "data": "Hello",
                "encoding": "utf-8",
                "mode": "binary",
            },
            "test.yml",
            10,
        )

        Base64.Validators.validate_encode(sv, context)

        assert len(context.warnings) >= 1
        warning_msg = context.warnings[0].message.lower()
        assert "unknown parameter" in warning_msg
        assert "encoding" in warning_msg or "mode" in warning_msg
