"""Unit tests for validation_utils.py"""

from unittest.mock import MagicMock
from snowfakery.utils.validation_utils import get_fuzzy_match, resolve_value
from snowfakery.data_generator_runtime_object_model import SimpleValue, StructuredValue
from snowfakery.recipe_validator import ValidationContext
import jinja2
from jinja2 import nativetypes


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
        # Very strict cutoff (0.9) - "tset" vs "test" has ratio 0.75, so won't match
        result = get_fuzzy_match("tset", available, cutoff=0.9)
        assert result is None

        # Lower cutoff (0.6) - should match
        result = get_fuzzy_match("tset", available, cutoff=0.6)
        assert result == "test"

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
        """Test resolving SimpleValue with Jinja template (without interpreter)"""
        context = ValidationContext()
        simple_val = SimpleValue("${{count + 1}}", "test.yml", 10)
        # Returns None when interpreter not set (can't execute Jinja)
        result = resolve_value(simple_val, context)
        assert result is None

    def test_resolve_structured_value_without_interpreter(self):
        """Test resolving StructuredValue without interpreter"""
        context = ValidationContext()
        struct_val = StructuredValue(
            "random_number", {"min": 1, "max": 10}, "test.yml", 10
        )
        # Returns None when interpreter not set
        result = resolve_value(struct_val, context)
        assert result is None

    def test_resolve_unsupported_type(self):
        """Test resolving unsupported type"""
        context = ValidationContext()
        result = resolve_value({"key": "value"}, context)
        assert result is None

    def test_resolve_mock_value(self):
        """Test that mock values return None"""
        context = ValidationContext()
        result = resolve_value("<mock_value>", context)
        assert result is None

    def test_resolve_simple_value_with_mock_string(self):
        """Test that mock strings in SimpleValue are returned as-is (not filtered)"""
        context = ValidationContext()
        simple_val = SimpleValue("<mock_test>", "test.yml", 10)
        # Mock values in literal strings are returned as-is
        # Only Jinja-resolved mock values return None
        result = resolve_value(simple_val, context)
        assert result == "<mock_test>"


class TestResolveValueWithInterpreter:
    """Test resolve_value with full interpreter setup"""

    def setup_context_with_interpreter(self):
        """Create a ValidationContext with mocked interpreter"""
        context = ValidationContext()

        # Mock interpreter
        mock_interpreter = MagicMock()

        # Mock standard_funcs with actual function
        def mock_random_number(min=0, max=10, step=1):
            return 5  # Return fixed value for testing

        mock_interpreter.standard_funcs = {
            "random_number": mock_random_number,
            "if_": lambda condition, true_val, false_val: true_val
            if condition
            else false_val,
        }

        # Mock plugin_instances
        mock_plugin = MagicMock()
        mock_funcs = MagicMock()
        mock_funcs.sqrt = lambda x: x**0.5
        mock_plugin.custom_functions.return_value = mock_funcs
        mock_interpreter.plugin_instances = {"Math": mock_plugin}

        # Set up template evaluator factory
        mock_evaluator_factory = MagicMock()
        mock_interpreter.template_evaluator_factory = mock_evaluator_factory

        # Set up Jinja environment
        context.jinja_env = nativetypes.NativeEnvironment(
            block_start_string="${%",
            block_end_string="%}",
            variable_start_string="${{",
            variable_end_string="}}",
            undefined=jinja2.StrictUndefined,
        )

        context.interpreter = mock_interpreter
        context.current_template = MagicMock(filename="test.yml", line_num=10)

        return context

    def test_resolve_jinja_with_interpreter(self):
        """Test resolving Jinja template with interpreter"""
        context = self.setup_context_with_interpreter()

        # Add a variable to the context
        context.available_variables["test_var"] = 100
        context._variable_cache["test_var"] = 100

        simple_val = SimpleValue("${{test_var + 1}}", "test.yml", 10)
        result = resolve_value(simple_val, context)

        # Jinja templates are executed via validate_jinja_template_by_execution
        # Should resolve to the calculated value
        assert result == 101  # test_var (100) + 1

    def test_resolve_jinja_that_returns_mock(self):
        """Test that Jinja-resolved mock values return None"""
        context = self.setup_context_with_interpreter()

        # When Jinja resolves to a mock value (from fake.unknown_provider),
        # it should trigger an error in the validation context
        simple_val = SimpleValue("${{fake.unknown_provider}}", "test.yml", 10)
        result = resolve_value(simple_val, context)

        # Should return None and add an error about unknown provider
        assert result is None
        # Check that an error was added about the unknown provider
        assert len(context.errors) > 0
        assert "unknown_provider" in str(context.errors[0].message).lower()

    def test_resolve_structured_value_with_interpreter(self):
        """Test resolving StructuredValue with interpreter"""
        context = self.setup_context_with_interpreter()

        # Create StructuredValue with literal arguments
        struct_val = StructuredValue(
            "random_number", {"min": 1, "max": 10}, "test.yml", 10
        )

        result = resolve_value(struct_val, context)
        # Should return the actual function result (5 from our mock)
        assert result == 5

    def test_resolve_structured_value_with_nested_args(self):
        """Test resolving StructuredValue with nested StructuredValue args"""
        context = self.setup_context_with_interpreter()

        # Create nested StructuredValues
        inner_struct = StructuredValue(
            "random_number", {"min": 50, "max": 100}, "test.yml", 10
        )

        outer_struct = StructuredValue(
            "random_number", {"min": 1, "max": inner_struct}, "test.yml", 11
        )

        result = resolve_value(outer_struct, context)
        # Should recursively resolve inner, then outer
        assert result == 5  # Our mock returns 5

    def test_resolve_structured_value_with_unresolvable_arg(self):
        """Test StructuredValue with argument that can't be resolved"""
        context = self.setup_context_with_interpreter()

        # Create an unresolvable argument (e.g., another object)
        unresolvable_arg = {"complex": "object"}

        struct_val = StructuredValue(
            "random_number", {"min": 1, "max": unresolvable_arg}, "test.yml", 10
        )

        result = resolve_value(struct_val, context)
        # Dict arguments get passed through - the function will try to execute with them
        # Since random_number expects int but gets dict, it will raise an exception
        # and resolve_value will return None
        assert result is None

    def test_resolve_structured_value_plugin_function(self):
        """Test resolving StructuredValue that calls plugin function"""
        context = self.setup_context_with_interpreter()

        struct_val = StructuredValue("sqrt", [25], "test.yml", 10)

        result = resolve_value(struct_val, context)
        # Should execute the plugin function
        assert result == 5.0  # sqrt(25) = 5.0

    def test_resolve_structured_value_with_kwargs(self):
        """Test resolving StructuredValue with keyword arguments"""
        context = self.setup_context_with_interpreter()

        # Create StructuredValue with SimpleValue in kwargs
        simple_min = SimpleValue(5, "test.yml", 10)
        simple_max = SimpleValue(15, "test.yml", 11)

        struct_val = StructuredValue(
            "random_number", {"min": simple_min, "max": simple_max}, "test.yml", 12
        )

        result = resolve_value(struct_val, context)
        assert result == 5  # Our mock returns 5

    def test_resolve_structured_value_function_not_found(self):
        """Test StructuredValue with function that doesn't exist"""
        context = self.setup_context_with_interpreter()

        struct_val = StructuredValue("nonexistent_function", {"arg": 1}, "test.yml", 10)

        result = resolve_value(struct_val, context)
        # Should return None when function not found
        assert result is None

    def test_resolve_structured_value_function_raises_exception(self):
        """Test StructuredValue when function execution raises exception"""
        context = self.setup_context_with_interpreter()

        # Add a function that raises an exception
        def failing_func(*args, **kwargs):
            raise ValueError("Test error")

        context.interpreter.standard_funcs["failing_func"] = failing_func

        struct_val = StructuredValue("failing_func", {}, "test.yml", 10)

        result = resolve_value(struct_val, context)
        # Should return None when function raises exception
        assert result is None

    def test_resolve_jinja_that_resolves_to_mock_value(self):
        """Test that Jinja templates resolving to mock values return None"""
        context = self.setup_context_with_interpreter()

        # Mock the validate_jinja_template_by_execution to return a mock value
        from unittest.mock import patch

        with patch(
            "snowfakery.recipe_validator.validate_jinja_template_by_execution"
        ) as mock_validate:
            mock_validate.return_value = "<mock_result>"

            simple_val = SimpleValue("${{fake.unknown_provider}}", "test.yml", 10)
            result = resolve_value(simple_val, context)

            # Should return None when Jinja resolves to mock value
            assert result is None

    def test_resolve_structured_value_with_unresolvable_nested_arg(self):
        """Test StructuredValue with nested arg that cannot be resolved"""
        context = self.setup_context_with_interpreter()

        # Create a nested StructuredValue that will return None (in args, not kwargs)
        inner_struct = StructuredValue(
            "nonexistent_func", {}, "test.yml", 10  # This will return None
        )

        # Use args instead of kwargs to cover line 106
        outer_struct = StructuredValue(
            "random_number",
            [1, inner_struct],  # args: min=1, max=inner_struct
            "test.yml",
            11,
        )

        result = resolve_value(outer_struct, context)
        # Should return None when nested arg cannot be resolved
        assert result is None
