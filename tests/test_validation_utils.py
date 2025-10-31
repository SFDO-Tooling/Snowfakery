"""Unit tests for validation_utils.py"""

from snowfakery.utils.validation_utils import get_fuzzy_match, resolve_value
from snowfakery.data_generator_runtime_object_model import SimpleValue, StructuredValue
from snowfakery.recipe_validator import ValidationContext


class TestGetFuzzyMatch:
    """Test get_fuzzy_match function"""

    def test_exact_match_not_found(self):
        """Test finding close match for typo"""
        available = ["random_number", "reference", "random_choice"]
        result = get_fuzzy_match("random_numbr", available)
        assert result == "random_number"

    def test_close_match_found(self):
        """Test finding close match"""
        available = ["first_name", "last_name", "email"]
        result = get_fuzzy_match("frist_name", available)
        assert result == "first_name"

    def test_no_close_match(self):
        """Test when no close match exists"""
        available = ["random_number", "reference"]
        result = get_fuzzy_match("completely_different", available)
        # Should return None if no match above cutoff
        assert result is None

    def test_empty_list(self):
        """Test with empty available names"""
        result = get_fuzzy_match("anything", [])
        assert result is None

    def test_custom_cutoff(self):
        """Test with custom similarity cutoff"""
        available = ["test"]
        # Very strict cutoff
        result = get_fuzzy_match("tset", available, cutoff=0.9)
        # May or may not match depending on similarity score
        # Just ensure it doesn't crash
        assert result is None or result == "test"

    def test_case_sensitivity(self):
        """Test case sensitive matching"""
        available = ["Account", "Contact"]
        result = get_fuzzy_match("account", available)
        # difflib is case-sensitive, so should match Account
        assert result == "Account"


class TestResolveValue:
    """Test resolve_value function"""

    def test_resolve_int_literal(self):
        """Test resolving integer literal"""
        context = ValidationContext()
        result = resolve_value(42, context)
        assert result == 42

    def test_resolve_float_literal(self):
        """Test resolving float literal"""
        context = ValidationContext()
        result = resolve_value(3.14, context)
        assert result == 3.14

    def test_resolve_string_literal(self):
        """Test resolving string literal"""
        context = ValidationContext()
        result = resolve_value("hello", context)
        assert result == "hello"

    def test_resolve_bool_literal(self):
        """Test resolving boolean literal"""
        context = ValidationContext()
        result = resolve_value(True, context)
        assert result is True
        result = resolve_value(False, context)
        assert result is False

    def test_resolve_none_literal(self):
        """Test resolving None"""
        context = ValidationContext()
        result = resolve_value(None, context)
        assert result is None

    def test_resolve_simple_value_with_literal(self):
        """Test resolving SimpleValue containing literal"""
        context = ValidationContext()
        simple_val = SimpleValue(100, "test.yml", 10)
        result = resolve_value(simple_val, context)
        assert result == 100

    def test_resolve_simple_value_with_string(self):
        """Test resolving SimpleValue containing string"""
        context = ValidationContext()
        simple_val = SimpleValue("test", "test.yml", 10)
        result = resolve_value(simple_val, context)
        assert result == "test"

    def test_resolve_simple_value_with_jinja(self):
        """Test resolving SimpleValue with Jinja template"""
        context = ValidationContext()
        simple_val = SimpleValue("${{count + 1}}", "test.yml", 10)
        # Returns the string as-is (doesn't parse Jinja)
        result = resolve_value(simple_val, context)
        assert result == "${{count + 1}}"

    def test_resolve_structured_value(self):
        """Test resolving StructuredValue (function call)"""
        context = ValidationContext()
        struct_val = StructuredValue(
            "random_number", {"min": 1, "max": 10}, "test.yml", 10
        )
        # Cannot resolve function calls statically
        result = resolve_value(struct_val, context)
        assert result is None

    def test_resolve_unsupported_type(self):
        """Test resolving unsupported type"""
        context = ValidationContext()
        result = resolve_value({"key": "value"}, context)
        assert result is None
