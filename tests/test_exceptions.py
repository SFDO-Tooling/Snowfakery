from snowfakery.data_gen_exceptions import DataGenError, DataGenValidationError
from snowfakery.recipe_validator import (
    ValidationResult,
    ValidationError,
    ValidationWarning,
)


class TestExceptions:
    def test_stringify_DataGenError(self):
        val = str(DataGenError("Blah", "foo.yml", 25))
        assert "Blah" in val
        assert "foo.yml" in val
        assert "25" in val

        val = str(DataGenError("Blah", "foo.yml"))
        assert "Blah" in val
        assert "foo.yml" in val


class TestDataGenValidationError:
    """Test DataGenValidationError exception class"""

    def test_init_with_errors(self):
        """Test initialization with validation errors"""
        error = ValidationError("Test error message", "test.yml", 10)
        result = ValidationResult(errors=[error])

        exc = DataGenValidationError(result)

        assert exc.validation_result == result
        assert exc.message == "Test error message"

    def test_init_with_no_errors(self):
        """Test initialization with empty validation result"""
        result = ValidationResult()

        exc = DataGenValidationError(result)

        assert exc.validation_result == result
        assert exc.message == "Recipe validation failed"

    def test_str_with_single_error(self):
        """Test string representation with single error"""
        error = ValidationError("Test error", "test.yml", 10)
        result = ValidationResult(errors=[error])

        exc = DataGenValidationError(result)
        exc_str = str(exc)

        assert "Test error" in exc_str
        assert "test.yml" in exc_str
        assert "10" in exc_str

    def test_str_with_multiple_errors(self):
        """Test string representation with multiple errors"""
        error1 = ValidationError("First error", "test.yml", 10)
        error2 = ValidationError("Second error", "test.yml", 20)
        result = ValidationResult(errors=[error1, error2])

        exc = DataGenValidationError(result)
        exc_str = str(exc)

        assert "First error" in exc_str
        assert "Second error" in exc_str

    def test_str_with_errors_and_warnings(self):
        """Test string representation with both errors and warnings"""
        error = ValidationError("Error message", "test.yml", 10)
        warning = ValidationWarning("Warning message", "test.yml", 15)
        result = ValidationResult(errors=[error], warnings=[warning])

        exc = DataGenValidationError(result)
        exc_str = str(exc)

        assert "Error message" in exc_str
        assert "Warning message" in exc_str

    def test_prefix_attribute(self):
        """Test that the prefix attribute is set"""
        result = ValidationResult()
        exc = DataGenValidationError(result)

        assert hasattr(exc, "prefix")
        assert "validation" in exc.prefix.lower()

    def test_inherits_from_DataGenError(self):
        """Test that DataGenValidationError inherits from DataGenError"""
        result = ValidationResult()
        exc = DataGenValidationError(result)

        assert isinstance(exc, DataGenError)
        assert isinstance(exc, Exception)
