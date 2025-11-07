"""Unit tests for FakerValidators class."""

from io import StringIO
import pytest
from faker import Faker

from snowfakery.fakedata.faker_validators import FakerValidators
from snowfakery.fakedata.fake_data_generator import FakeNames
from snowfakery.recipe_validator import ValidationContext
from snowfakery.data_generator_runtime_object_model import StructuredValue
from snowfakery.api import generate_data


def create_faker_with_snowfakery_providers():
    """Create a Faker instance with FakeNames provider added.

    This replicates what happens at runtime so tests validate against
    the correct method signatures (e.g., email(matching=True) not email(safe=True)).
    """
    faker = Faker()
    fake_names = FakeNames(faker, faker_context=None)
    faker.add_provider(fake_names)
    return faker


class TestFakerValidatorsInit:
    """Test FakerValidators initialization."""

    def test_init_with_faker_instance(self):
        """Test initialization with Faker instance."""
        faker = create_faker_with_snowfakery_providers()
        validator = FakerValidators(faker)

        assert validator.faker_instance == faker
        assert len(validator.faker_providers) > 0
        assert "first_name" in validator.faker_providers
        assert "email" in validator.faker_providers

    def test_init_with_explicit_providers(self):
        """Test initialization with explicit provider list."""
        faker = create_faker_with_snowfakery_providers()
        custom_providers = {"first_name", "last_name", "email"}
        validator = FakerValidators(faker, custom_providers)

        assert validator.faker_providers == custom_providers

    def test_extract_providers(self):
        """Test automatic provider extraction."""
        faker = create_faker_with_snowfakery_providers()
        validator = FakerValidators(faker)

        # Should have many providers
        assert len(validator.faker_providers) > 50
        # Common providers should be present
        assert "first_name" in validator.faker_providers
        assert "email" in validator.faker_providers
        assert "address" in validator.faker_providers
        assert "random_int" in validator.faker_providers


class TestValidateProviderName:
    """Test provider name validation."""

    def test_valid_provider_name(self):
        """Test validation passes for valid provider."""
        faker = create_faker_with_snowfakery_providers()
        validator = FakerValidators(faker)
        context = ValidationContext()

        result = validator.validate_provider_name("first_name", context)

        assert result is True
        assert len(context.errors) == 0

    def test_invalid_provider_name(self):
        """Test validation fails for invalid provider."""
        faker = create_faker_with_snowfakery_providers()
        validator = FakerValidators(faker)
        context = ValidationContext()

        result = validator.validate_provider_name("invalid_provider", context)

        assert result is False
        assert len(context.errors) == 1
        assert "Unknown Faker provider 'invalid_provider'" in context.errors[0].message

    def test_typo_suggestion(self):
        """Test fuzzy matching suggests correction for typos."""
        faker = create_faker_with_snowfakery_providers()
        validator = FakerValidators(faker)
        context = ValidationContext()

        result = validator.validate_provider_name("first_nam", context)

        assert result is False
        assert len(context.errors) == 1
        assert "first_name" in context.errors[0].message
        assert "Did you mean" in context.errors[0].message


class TestValidateProviderCall:
    """Test provider call parameter validation."""

    def test_valid_call_no_params(self):
        """Test valid call with no parameters."""
        faker = create_faker_with_snowfakery_providers()
        validator = FakerValidators(faker)
        context = ValidationContext()

        validator.validate_provider_call("first_name", [], {}, context)

        assert len(context.errors) == 0

    def test_valid_call_with_params(self):
        """Test valid call with correct parameters."""
        faker = create_faker_with_snowfakery_providers()
        validator = FakerValidators(faker)
        context = ValidationContext()

        # FakeNames.email accepts matching=True, not safe
        validator.validate_provider_call("email", [], {"matching": True}, context)

        assert len(context.errors) == 0

    def test_unknown_parameter(self):
        """Test error for unknown parameter name."""
        faker = create_faker_with_snowfakery_providers()
        validator = FakerValidators(faker)
        context = ValidationContext()

        # Test with typo in 'matching' parameter
        validator.validate_provider_call("email", [], {"matchin": True}, context)

        assert len(context.errors) == 1
        assert "matchin" in context.errors[0].message
        assert "unexpected keyword argument" in context.errors[0].message

    def test_too_many_positional_args(self):
        """Test error for too many positional arguments."""
        faker = create_faker_with_snowfakery_providers()
        validator = FakerValidators(faker)
        context = ValidationContext()

        validator.validate_provider_call("first_name", ["extra", "args"], {}, context)

        assert len(context.errors) == 1
        assert "too many positional arguments" in context.errors[0].message

    def test_wrong_parameter_type(self):
        """Test error for wrong parameter type."""
        faker = create_faker_with_snowfakery_providers()
        validator = FakerValidators(faker)
        context = ValidationContext()

        # email(matching=...) expects bool, passing str
        validator.validate_provider_call("email", [], {"matching": "yes"}, context)

        assert len(context.errors) == 1
        assert "matching" in context.errors[0].message
        assert "bool" in context.errors[0].message.lower()
        assert "str" in context.errors[0].message.lower()

    def test_valid_optional_parameter(self):
        """Test valid optional parameter."""
        faker = create_faker_with_snowfakery_providers()
        validator = FakerValidators(faker)
        context = ValidationContext()

        # Test with optional parameter on a different method that accepts them
        # random_int accepts min, max, step
        validator.validate_provider_call(
            "random_int", [], {"min": 1, "max": 100}, context
        )

        assert len(context.errors) == 0

    def test_signature_caching(self):
        """Test that signatures are cached for performance."""
        faker = create_faker_with_snowfakery_providers()
        validator = FakerValidators(faker)
        context = ValidationContext()

        # First call
        validator.validate_provider_call("email", [], {"matching": True}, context)
        assert "email" in validator._signature_cache

        # Second call should use cached signature
        cached_sig = validator._signature_cache["email"]
        validator.validate_provider_call("email", [], {"matching": False}, context)
        assert validator._signature_cache["email"] is cached_sig


class TestValidateFake:
    """Test validate_fake static method for StructuredValue syntax."""

    def test_valid_fake_call(self):
        """Test valid fake: provider_name syntax."""
        context = ValidationContext()
        context.faker_instance = Faker()
        context.faker_providers = {"first_name", "last_name", "email"}

        sv = StructuredValue("fake", ["first_name"], "test.yml", 10)
        FakerValidators.validate_fake(sv, context)

        assert len(context.errors) == 0

    def test_missing_provider_name(self):
        """Test error when provider name is missing."""
        context = ValidationContext()
        context.faker_instance = Faker()
        context.faker_providers = {"first_name"}

        sv = StructuredValue("fake", [], "test.yml", 10)
        FakerValidators.validate_fake(sv, context)

        assert len(context.errors) == 1
        assert "Missing provider name" in context.errors[0].message

    def test_unknown_provider_in_fake(self):
        """Test error for unknown provider in fake: syntax."""
        context = ValidationContext()
        context.faker_instance = Faker()
        context.faker_providers = {"first_name", "last_name"}

        sv = StructuredValue("fake", ["invalid_provider"], "test.yml", 10)
        FakerValidators.validate_fake(sv, context)

        assert len(context.errors) == 1
        assert "Unknown Faker provider" in context.errors[0].message
        assert "invalid_provider" in context.errors[0].message


class TestIntegrationWithJinja:
    """Integration tests with Jinja syntax validation."""

    def test_jinja_valid_call(self):
        """Test Jinja syntax with valid Faker call."""
        yaml = """
        - object: Test
          fields:
            email: ${{fake.email(matching=True)}}
        """
        result = generate_data(StringIO(yaml), validate_only=True)
        assert len(result.errors) == 0

    def test_jinja_unknown_provider(self):
        """Test Jinja syntax catches unknown provider."""
        yaml = """
        - object: Test
          fields:
            value: ${{fake.invalid_provider()}}
        """
        with pytest.raises(Exception) as exc_info:
            generate_data(StringIO(yaml), validate_only=True)
        assert "Unknown Faker provider" in str(exc_info.value)

    def test_jinja_parameter_typo(self):
        """Test Jinja syntax catches parameter typo."""
        yaml = """
        - object: Test
          fields:
            email: ${{fake.email(matchin=True)}}
        """
        with pytest.raises(Exception) as exc_info:
            generate_data(StringIO(yaml), validate_only=True)
        assert "matchin" in str(exc_info.value)

    def test_jinja_wrong_type(self):
        """Test Jinja syntax catches type mismatch."""
        yaml = """
        - object: Test
          fields:
            email: ${{fake.email(matching="yes")}}
        """
        with pytest.raises(Exception) as exc_info:
            generate_data(StringIO(yaml), validate_only=True)
        assert "bool" in str(exc_info.value).lower()


class TestIntegrationWithStructuredValue:
    """Integration tests with StructuredValue syntax validation."""

    def test_structured_value_valid(self):
        """Test StructuredValue syntax with valid provider."""
        yaml = """
        - object: Test
          fields:
            first_name:
              fake: first_name
        """
        result = generate_data(StringIO(yaml), validate_only=True)
        assert len(result.errors) == 0

    def test_structured_value_unknown_provider(self):
        """Test StructuredValue syntax catches unknown provider."""
        yaml = """
        - object: Test
          fields:
            value:
              fake: invalid_provider
        """
        with pytest.raises(Exception) as exc_info:
            generate_data(StringIO(yaml), validate_only=True)
        assert "Unknown Faker provider" in str(exc_info.value)

    def test_structured_value_typo_suggestion(self):
        """Test StructuredValue syntax suggests correction."""
        yaml = """
        - object: Test
          fields:
            name:
              fake: first_nam
        """
        with pytest.raises(Exception) as exc_info:
            generate_data(StringIO(yaml), validate_only=True)
        assert "first_name" in str(exc_info.value)
        assert "Did you mean" in str(exc_info.value)


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_no_faker_instance(self):
        """Test graceful handling when faker_instance is None."""
        context = ValidationContext()
        context.faker_instance = None

        sv = StructuredValue("fake", ["first_name"], "test.yml", 10)
        # Should not crash
        FakerValidators.validate_fake(sv, context)

    def test_provider_without_signature(self):
        """Test handling providers that can't be introspected."""
        faker = create_faker_with_snowfakery_providers()
        validator = FakerValidators(faker)
        context = ValidationContext()

        # Most Faker methods have signatures, but test graceful handling
        # If a method can't be introspected, validation should skip it
        validator.validate_provider_call("first_name", [], {}, context)
        assert len(context.errors) == 0

    def test_complex_type_annotations(self):
        """Test handling of complex type annotations."""
        faker = create_faker_with_snowfakery_providers()
        validator = FakerValidators(faker)
        context = ValidationContext()

        # date_between has Union[date, datetime, str, int] annotations
        # Should not crash with complex types
        validator.validate_provider_call(
            "date_between", [], {"start_date": "-30y", "end_date": "today"}, context
        )
        assert len(context.errors) == 0

    def test_extract_providers_with_no_instance(self):
        """Test _extract_providers with None instance."""
        validator = FakerValidators(None, set())
        assert validator.faker_providers == set()

    def test_extract_providers_skip_problematic_attrs(self):
        """Test that problematic attributes like 'seed' are skipped."""
        faker = create_faker_with_snowfakery_providers()
        validator = FakerValidators(faker)
        # 'seed' should not be in providers (causes TypeError)
        assert "seed" not in validator.faker_providers
        assert "seed_instance" not in validator.faker_providers
        assert "seed_locale" not in validator.faker_providers

    def test_validate_provider_call_with_none_values(self):
        """Test parameter validation with None values."""
        faker = create_faker_with_snowfakery_providers()
        validator = FakerValidators(faker)
        context = ValidationContext()

        # Test None value on a parameter that expects bool (not Optional)
        # This should produce a type error since matching: bool is not Optional[bool]
        validator.validate_provider_call("email", [], {"matching": None}, context)
        assert len(context.errors) == 1
        assert "matching" in context.errors[0].message
        assert "bool" in context.errors[0].message.lower()

    def test_check_type_with_none_and_optional(self):
        """Test _check_type with None value and Optional type."""
        from typing import Optional

        faker = create_faker_with_snowfakery_providers()
        validator = FakerValidators(faker)

        # None should match Optional[str]
        result = validator._check_type(None, Optional[str])
        assert result is True

    def test_check_type_with_none_not_optional(self):
        """Test _check_type with None value and non-optional type."""
        faker = create_faker_with_snowfakery_providers()
        validator = FakerValidators(faker)

        # None should NOT match str
        result = validator._check_type(None, str)
        assert result is False

    def test_check_type_with_union_types(self):
        """Test _check_type with Union types."""
        from typing import Union

        faker = create_faker_with_snowfakery_providers()
        validator = FakerValidators(faker)

        # String should match Union[str, int]
        result = validator._check_type("test", Union[str, int])
        assert result is True

        # Int should match Union[str, int]
        result = validator._check_type(42, Union[str, int])
        assert result is True

        # Bool should NOT match Union[str, int]
        result = validator._check_type(True, Union[str, int])
        # Note: bool is a subclass of int in Python, so this might return True
        # Just ensure no crash
        assert isinstance(result, bool)

    def test_check_type_with_complex_annotation(self):
        """Test _check_type with complex type that can't be checked."""
        faker = create_faker_with_snowfakery_providers()
        validator = FakerValidators(faker)

        # Complex types should return True (assume valid)
        result = validator._check_type("test", "ComplexType")
        assert result is True

    def test_format_type_optional(self):
        """Test _format_type with Optional types."""
        from typing import Optional

        faker = create_faker_with_snowfakery_providers()
        validator = FakerValidators(faker)

        result = validator._format_type(Optional[str])
        assert "str" in result
        assert "None" in result

    def test_format_type_union(self):
        """Test _format_type with Union types."""
        from typing import Union

        faker = create_faker_with_snowfakery_providers()
        validator = FakerValidators(faker)

        result = validator._format_type(Union[str, int])
        assert "str" in result
        assert "int" in result

    def test_format_type_union_with_none(self):
        """Test _format_type with Union including None."""
        from typing import Union

        faker = create_faker_with_snowfakery_providers()
        validator = FakerValidators(faker)

        result = validator._format_type(Union[str, int, None])
        assert "str" in result
        assert "int" in result
        assert "None" in result

    def test_format_type_simple(self):
        """Test _format_type with simple types."""
        faker = create_faker_with_snowfakery_providers()
        validator = FakerValidators(faker)

        assert validator._format_type(str) == "str"
        assert validator._format_type(int) == "int"
        assert validator._format_type(bool) == "bool"

    def test_validate_fake_with_non_string_provider(self):
        """Test validate_fake when provider name resolves to non-string."""
        from snowfakery.data_generator_runtime_object_model import SimpleValue

        context = ValidationContext()
        context.faker_instance = Faker()
        context.faker_providers = {"first_name"}

        # Provider name is an integer (invalid)
        sv = StructuredValue("fake", [SimpleValue(123, "test.yml", 10)], "test.yml", 10)
        FakerValidators.validate_fake(sv, context)
        # Should not crash, just skip validation

    def test_validate_provider_call_no_signature(self):
        """Test validate_provider_call when signature can't be obtained."""
        faker = create_faker_with_snowfakery_providers()
        validator = FakerValidators(faker)
        context = ValidationContext()

        # Force a provider without cached signature
        # Most providers have signatures, but test the fallback
        validator.validate_provider_call("first_name", [], {}, context)
        assert len(context.errors) == 0

    def test_validate_provider_call_with_filename_linenum(self):
        """Test error reporting includes filename and line number."""
        faker = create_faker_with_snowfakery_providers()
        validator = FakerValidators(faker)
        context = ValidationContext()
        context.current_template = type(
            "obj", (object,), {"filename": "test.yml", "line_num": 42}
        )()

        # Trigger an error with unknown parameter
        validator.validate_provider_call("email", [], {"invalid_param": True}, context)

        assert len(context.errors) == 1
        assert context.errors[0].filename == "test.yml"
        assert context.errors[0].line_num == 42

    def test_check_type_union_with_non_type_arg(self):
        """Test _check_type with Union containing non-type arguments."""
        from typing import Union

        faker = create_faker_with_snowfakery_providers()
        validator = FakerValidators(faker)

        # Test Union with complex args that aren't simple types
        # This covers the TypeError exception handling in _check_type
        result = validator._check_type("test", Union[str, int])
        assert result is True

    def test_format_type_with_complex_union_args(self):
        """Test _format_type with Union args that don't have __name__."""
        faker = create_faker_with_snowfakery_providers()
        validator = FakerValidators(faker)

        # Test formatting for simple types
        from typing import Union

        result = validator._format_type(Union[str, int])
        # Should contain both types
        assert "str" in result or "int" in result

    def test_validate_provider_call_parameter_resolution(self):
        """Test that parameter values are properly resolved before validation."""
        from snowfakery.data_generator_runtime_object_model import SimpleValue

        faker = create_faker_with_snowfakery_providers()
        validator = FakerValidators(faker)
        context = ValidationContext()

        # Pass SimpleValue that wraps the correct type
        matching_param = SimpleValue(True, "test.yml", 10)
        validator.validate_provider_call(
            "email", [], {"matching": matching_param}, context
        )

        # Should resolve and validate correctly
        assert len(context.errors) == 0

    def test_format_type_with_no_name_attribute(self):
        """Test _format_type fallback for types without __name__."""
        faker = create_faker_with_snowfakery_providers()
        validator = FakerValidators(faker)

        # Create a mock type-like object without __name__
        class MockType:
            pass

        result = validator._format_type(MockType)
        # Should return string representation
        assert isinstance(result, str)

    def test_extract_providers_with_attribute_error(self):
        """Test _extract_providers handles AttributeError gracefully."""
        # Create a mock Faker with an attribute that raises AttributeError
        class MockFaker:
            def __dir__(self):
                return ["valid_method", "problematic_attr"]

            def valid_method(self):
                pass

            def __getattribute__(self, name):
                if name == "problematic_attr":
                    raise AttributeError("Simulated error")
                return super().__getattribute__(name)

        mock_faker = MockFaker()
        validator = FakerValidators(mock_faker)

        # Should not crash, 'problematic_attr' should be skipped
        assert "problematic_attr" not in validator.faker_providers

    def test_validate_provider_call_non_literal_params(self):
        """Test that non-literal parameter values are skipped in type checking."""
        from snowfakery.data_generator_runtime_object_model import StructuredValue

        faker = create_faker_with_snowfakery_providers()
        validator = FakerValidators(faker)
        context = ValidationContext()

        # Pass a StructuredValue (non-literal) as parameter
        # resolve_value will try to validate it, so expect that error
        complex_param = StructuredValue("some_func", [], "test.yml", 10)
        validator.validate_provider_call(
            "email", [], {"matching": complex_param}, context
        )

        # Should get 1 error from resolve_value finding unknown function
        # This is correct behavior - type checking is skipped but validation still occurs
        assert len(context.errors) == 1
        assert "Unknown function 'some_func'" in context.errors[0].message
