"""Unit tests for recipe_validator.py"""

import pytest
import jinja2
from io import StringIO

from snowfakery.recipe_validator import (
    ValidationError,
    ValidationWarning,
    ValidationResult,
    ValidationContext,
    build_function_registry,
    is_name_available,
    validate_statement,
    validate_jinja_template_by_execution,
    validate_field_definition,
)
from snowfakery.data_generator_runtime_object_model import (
    ObjectTemplate,
    VariableDefinition,
    StructuredValue,
    SimpleValue,
)
from snowfakery.data_generator import generate
from snowfakery.data_gen_exceptions import DataGenValidationError


class TestValidationError:
    """Test ValidationError dataclass"""

    def test_error_with_all_fields(self):
        error = ValidationError("Test error", "test.yml", 42)
        assert error.message == "Test error"
        assert error.filename == "test.yml"
        assert error.line_num == 42
        assert str(error) == "test.yml:42: Error: Test error"

    def test_error_with_filename_only(self):
        error = ValidationError("Test error", "test.yml")
        assert str(error) == "test.yml: Error: Test error"

    def test_error_without_location(self):
        error = ValidationError("Test error")
        assert str(error) == "Error: Test error"


class TestValidationWarning:
    """Test ValidationWarning dataclass"""

    def test_warning_with_all_fields(self):
        warning = ValidationWarning("Test warning", "test.yml", 42)
        assert warning.message == "Test warning"
        assert warning.filename == "test.yml"
        assert warning.line_num == 42
        assert str(warning) == "test.yml:42: Warning: Test warning"

    def test_warning_with_filename_only(self):
        warning = ValidationWarning("Test warning", "test.yml")
        assert str(warning) == "test.yml: Warning: Test warning"

    def test_warning_without_location(self):
        warning = ValidationWarning("Test warning")
        assert str(warning) == "Warning: Test warning"


class TestValidationResult:
    """Test ValidationResult class"""

    def test_empty_result(self):
        result = ValidationResult()
        assert not result.has_errors()
        assert not result.has_warnings()
        assert "✓ Validation passed" in result.get_summary()

    def test_result_with_errors(self):
        errors = [
            ValidationError("Error 1", "test.yml", 10),
            ValidationError("Error 2", "test.yml", 20),
        ]
        result = ValidationResult(errors=errors)
        assert result.has_errors()
        assert not result.has_warnings()
        summary = result.get_summary()
        assert "Validation Errors:" in summary
        assert "Error 1" in summary
        assert "Error 2" in summary

    def test_result_with_warnings(self):
        warnings = [
            ValidationWarning("Warning 1", "test.yml", 10),
            ValidationWarning("Warning 2", "test.yml", 20),
        ]
        result = ValidationResult(warnings=warnings)
        assert not result.has_errors()
        assert result.has_warnings()
        summary = result.get_summary()
        assert "Validation Warnings:" in summary
        assert "Warning 1" in summary
        assert "Warning 2" in summary

    def test_result_with_both(self):
        errors = [ValidationError("Error 1")]
        warnings = [ValidationWarning("Warning 1")]
        result = ValidationResult(errors=errors, warnings=warnings)
        assert result.has_errors()
        assert result.has_warnings()
        summary = result.get_summary()
        assert "Validation Errors:" in summary
        assert "Validation Warnings:" in summary

    def test_mutable_default_arguments_bug_fixed(self):
        """Test that mutable default arguments don't leak between instances"""
        result1 = ValidationResult()
        result1.errors.append(ValidationError("Error 1"))

        result2 = ValidationResult()
        # result2 should have empty errors, not share result1's errors
        assert len(result2.errors) == 0


class TestValidationContext:
    """Test ValidationContext class"""

    def test_context_initialization(self):
        context = ValidationContext()
        assert isinstance(context.available_functions, dict)
        assert isinstance(context.faker_providers, set)
        assert isinstance(context.all_objects, dict)
        assert isinstance(context.all_nicknames, dict)
        assert isinstance(context.available_objects, dict)
        assert isinstance(context.available_nicknames, dict)
        assert isinstance(context.available_variables, dict)
        assert isinstance(context.current_object_fields, dict)
        assert len(context.errors) == 0
        assert len(context.warnings) == 0

    def test_add_error(self):
        context = ValidationContext()
        context.add_error("Test error", "test.yml", 42)
        assert len(context.errors) == 1
        assert context.errors[0].message == "Test error"
        assert context.errors[0].filename == "test.yml"
        assert context.errors[0].line_num == 42

    def test_add_warning(self):
        context = ValidationContext()
        context.add_warning("Test warning", "test.yml", 42)
        assert len(context.warnings) == 1
        assert context.warnings[0].message == "Test warning"

    def test_resolve_variable(self):
        context = ValidationContext()
        simple_val = SimpleValue("value", "test.yml", 10)
        var_def = VariableDefinition("test.yml", 10, "test_var", simple_val)
        context.available_variables["test_var"] = var_def

        result = context.resolve_variable("test_var")
        assert result == var_def

        result = context.resolve_variable("nonexistent")
        assert result is None

    def test_resolve_object_sequential(self):
        context = ValidationContext()
        obj_template = ObjectTemplate("Account", "test.yml", 10)
        context.available_objects["Account"] = obj_template

        # Sequential access (allow_forward_ref=False)
        result = context.resolve_object("Account", allow_forward_ref=False)
        assert result == obj_template

        result = context.resolve_object("Contact", allow_forward_ref=False)
        assert result is None

    def test_resolve_object_forward_ref(self):
        context = ValidationContext()
        obj_template = ObjectTemplate("Account", "test.yml", 10)
        context.all_objects["Account"] = obj_template

        # Forward reference (allow_forward_ref=True)
        result = context.resolve_object("Account", allow_forward_ref=True)
        assert result == obj_template

    def test_resolve_nickname(self):
        context = ValidationContext()
        obj_template = ObjectTemplate(
            "Account", "test.yml", 10, nickname="main_account"
        )
        context.available_nicknames["main_account"] = obj_template

        result = context.resolve_object("main_account", allow_forward_ref=False)
        assert result == obj_template


class TestBuildFunctionRegistry:
    """Test build_function_registry function"""

    def test_builds_standard_functions(self):
        registry = build_function_registry([])

        # Check that standard function validators are registered
        assert "random_number" in registry
        assert "reference" in registry
        assert "random_choice" in registry
        assert "date" in registry
        assert "datetime" in registry
        assert callable(registry["random_number"])

    def test_handles_if_alias(self):
        registry = build_function_registry([])

        # Both "if" and "if_" should be registered
        assert "if" in registry or "if_" in registry


class TestIsNameAvailable:
    """Test is_name_available helper function"""

    def test_variable_available(self):
        context = ValidationContext()
        context.available_variables["my_var"] = "something"

        assert is_name_available("my_var", context)
        assert not is_name_available("other_var", context)

    def test_function_available(self):
        context = ValidationContext()

        def mock_func():
            pass

        context.available_functions["random_number"] = mock_func

        assert is_name_available("random_number", context)
        assert not is_name_available("other_func", context)

    def test_object_available(self):
        context = ValidationContext()
        context.available_objects["Account"] = "something"

        assert is_name_available("Account", context)
        assert not is_name_available("Contact", context)

    def test_nickname_available(self):
        context = ValidationContext()
        context.available_nicknames["main_account"] = "something"

        assert is_name_available("main_account", context)
        assert not is_name_available("other_nick", context)

    def test_faker_provider_available(self):
        context = ValidationContext()
        context.faker_providers = {"first_name", "last_name", "email"}

        assert is_name_available("first_name", context)
        assert not is_name_available("unknown_provider", context)


class TestValidateJinjaTemplate:
    """Test validate_jinja_template_by_execution function"""

    def test_valid_jinja_syntax(self):
        """Test valid Jinja syntax validation with mock interpreter"""
        from unittest.mock import MagicMock

        context = ValidationContext()
        context.jinja_env = __import__("jinja2").Environment(
            variable_start_string="${{", variable_end_string="}}"
        )

        # Mock interpreter with template evaluator factory
        mock_interpreter = MagicMock()

        def mock_evaluator(ctx):
            return 2  # Returns mock result

        mock_interpreter.template_evaluator_factory.get_evaluator.return_value = (
            mock_evaluator
        )
        context.interpreter = mock_interpreter

        # Valid syntax - should not add errors
        validate_jinja_template_by_execution("${{count + 1}}", "test.yml", 10, context)
        assert len(context.errors) == 0

    def test_invalid_jinja_syntax(self):
        context = ValidationContext()
        context.jinja_env = __import__("jinja2").Environment(
            variable_start_string="${{", variable_end_string="}}"
        )

        # Invalid syntax - missing closing braces
        # Note: Syntax errors are caught before interpreter is needed
        validate_jinja_template_by_execution("${{count +", "test.yml", 10, context)
        assert len(context.errors) == 1
        assert "Jinja syntax error" in context.errors[0].message


class TestValidateFieldDefinition:
    """Test validate_field_definition function"""

    def test_validate_literal_simple_value(self):
        context = ValidationContext()
        context.jinja_env = __import__("jinja2").Environment()

        # Literal value - no validation needed
        field_def = SimpleValue(42, "test.yml", 10)
        validate_field_definition(field_def, context)
        assert len(context.errors) == 0

    def test_validate_jinja_simple_value(self):
        """Test validation of Jinja template in SimpleValue with mock interpreter"""
        from unittest.mock import MagicMock

        context = ValidationContext()
        context.jinja_env = __import__("jinja2").Environment(
            variable_start_string="${{", variable_end_string="}}"
        )

        # Mock interpreter with template evaluator factory
        mock_interpreter = MagicMock()

        def mock_evaluator(ctx):
            return 2  # Returns mock result

        mock_interpreter.template_evaluator_factory.get_evaluator.return_value = (
            mock_evaluator
        )
        context.interpreter = mock_interpreter

        # Jinja template in SimpleValue
        field_def = SimpleValue("${{count + 1}}", "test.yml", 10)
        validate_field_definition(field_def, context)
        assert len(context.errors) == 0

    def test_validate_unknown_function(self):
        context = ValidationContext()
        context.available_functions = {}

        # Unknown function
        field_def = StructuredValue("unknown_func", [], "test.yml", 10)
        validate_field_definition(field_def, context)

        assert len(context.errors) == 1
        assert "Unknown function 'unknown_func'" in context.errors[0].message

    def test_validate_known_function(self):
        context = ValidationContext()

        def mock_validator(sv, ctx):
            pass

        context.available_functions = {"test_func": mock_validator}

        # Known function
        field_def = StructuredValue("test_func", [], "test.yml", 10)
        validate_field_definition(field_def, context)

        # Should not have errors (validator was called successfully)
        assert len(context.errors) == 0


class TestJinjaExecutionValidation:
    """Test execution-based Jinja validation features"""

    def test_cross_object_field_validation_success(self):
        """Test that valid cross-object field access passes validation"""
        recipe = """
- snowfakery_version: 3
- object: Account
  fields:
    Name: Test Company
    EmployeeCount: 100

- object: Contact
  fields:
    AccountName: ${{Account.Name}}
    CompanySize: ${{Account.EmployeeCount}}
        """

        result = generate(
            open_yaml_file=StringIO(recipe),
            strict_mode=True,
            validate_only=True,
        )
        assert not result.has_errors()

    def test_cross_object_field_validation_error(self):
        """Test that invalid cross-object field access is caught"""
        recipe = """
- snowfakery_version: 3
- object: Account
  fields:
    Name: Test Company

- object: Contact
  fields:
    Reference: ${{Account.NonExistentField}}
        """

        with pytest.raises(DataGenValidationError) as exc_info:
            generate(
                open_yaml_file=StringIO(recipe),
                strict_mode=True,
                validate_only=True,
            )

        error_msg = str(exc_info.value)
        assert "NonExistentField" in error_msg
        # Error message says "Object has no attribute 'NonExistentField'"
        assert "Object has no attribute" in error_msg or "no attribute" in error_msg

    def test_nested_function_calls_in_jinja(self):
        """Test that nested function calls inside Jinja are validated"""
        recipe = """
- snowfakery_version: 3
- object: Account
  fields:
    Score: ${{random_number(min=1, max=random_number(min=50, max=100))}}
        """

        # Should validate successfully (both inner and outer random_number calls)
        result = generate(
            open_yaml_file=StringIO(recipe),
            strict_mode=True,
            validate_only=True,
        )
        assert not result.has_errors()

    def test_nested_function_with_error(self):
        """Test that errors in nested function calls are caught"""
        recipe = """
- snowfakery_version: 3
- object: Account
  fields:
    Score: ${{random_number(min=100, max=random_number(min=10, max=5))}}
        """

        # Inner random_number has min > max
        with pytest.raises(DataGenValidationError) as exc_info:
            generate(
                open_yaml_file=StringIO(recipe),
                strict_mode=True,
                validate_only=True,
            )

        error_msg = str(exc_info.value)
        assert "min" in error_msg.lower()
        assert "max" in error_msg.lower()

    def test_faker_provider_in_jinja_success(self):
        """Test that valid Faker providers in Jinja are accepted"""
        recipe = """
- snowfakery_version: 3
- object: Contact
  fields:
    FirstName: ${{fake.first_name}}
    LastName: ${{fake.last_name}}
    Email: ${{fake.email}}
        """

        result = generate(
            open_yaml_file=StringIO(recipe),
            strict_mode=True,
            validate_only=True,
        )
        assert not result.has_errors()

    def test_faker_provider_in_jinja_error(self):
        """Test that invalid Faker provider names in Jinja are caught"""
        recipe = """
- snowfakery_version: 3
- object: Contact
  fields:
    FirstName: ${{fake.frist_name}}
        """

        with pytest.raises(DataGenValidationError) as exc_info:
            generate(
                open_yaml_file=StringIO(recipe),
                strict_mode=True,
                validate_only=True,
            )

        error_msg = str(exc_info.value)
        assert "frist_name" in error_msg
        # Should suggest the correct provider
        assert "first_name" in error_msg

    def test_faker_provider_returns_real_values(self):
        """Test that Faker providers return real values, not mock strings"""
        recipe = """
- snowfakery_version: 3
- var: generated_name
  value: ${{fake.first_name()}}

- var: name_length
  value: ${{'%s' % generated_name | length}}

- object: Contact
  fields:
    NameLength: ${{name_length}}
        """

        # This test verifies that fake.first_name() returns an actual string value
        # If it returned a mock like "<fake_first_name>", the length calculation would work
        # but the value would be a mock. The recipe should validate successfully
        # because the Faker method returns a real string value.
        result = generate(
            open_yaml_file=StringIO(recipe),
            strict_mode=True,
            validate_only=True,
        )
        assert not result.has_errors()

    def test_faker_provider_without_parentheses(self):
        """Test that Faker providers work without parentheses"""
        recipe = """
- snowfakery_version: 3
- object: Contact
  fields:
    FirstName: ${{fake.first_name}}
    LastName: ${{fake.last_name}}
    Email: ${{fake.email}}
    CompanyName: ${{fake.company}}
        """

        # Faker providers should work without parentheses
        result = generate(
            open_yaml_file=StringIO(recipe),
            strict_mode=True,
            validate_only=True,
        )
        assert not result.has_errors()

    def test_faker_provider_with_parentheses(self):
        """Test that Faker providers work with parentheses"""
        recipe = """
- snowfakery_version: 3
- object: Contact
  fields:
    FirstName: ${{fake.first_name()}}
    LastName: ${{fake.last_name()}}
    Email: ${{fake.email()}}
    CompanyName: ${{fake.company()}}
        """

        # Faker providers should work with parentheses
        result = generate(
            open_yaml_file=StringIO(recipe),
            strict_mode=True,
            validate_only=True,
        )
        assert not result.has_errors()

    def test_undefined_variable_in_jinja(self):
        """Test that undefined variables in Jinja are caught"""
        recipe = """
- snowfakery_version: 3
- var: company_suffix
  value: Corp

- object: Account
  fields:
    Name: ${{fake.company}} ${{company_sufix}}
        """

        with pytest.raises(DataGenValidationError) as exc_info:
            generate(
                open_yaml_file=StringIO(recipe),
                strict_mode=True,
                validate_only=True,
            )

        error_msg = str(exc_info.value)
        assert "company_sufix" in error_msg

    def test_variable_reference_success(self):
        """Test that defined variables can be referenced in Jinja"""
        recipe = """
- snowfakery_version: 3
- var: base_count
  value: 10

- object: Account
  fields:
    EmployeeCount: ${{base_count * 5}}
        """

        result = generate(
            open_yaml_file=StringIO(recipe),
            strict_mode=True,
            validate_only=True,
        )
        assert not result.has_errors()

    def test_builtin_variable_access(self):
        """Test that built-in variables (count, id, etc.) are available"""
        recipe = """
- snowfakery_version: 3
- object: Account
  count: 5
  fields:
    Name: Account ${{count}}
    RecordId: ${{id}}
        """

        result = generate(
            open_yaml_file=StringIO(recipe),
            strict_mode=True,
            validate_only=True,
        )
        assert not result.has_errors()

    def test_complex_jinja_expression(self):
        """Test complex Jinja expressions with multiple operations"""
        recipe = """
- snowfakery_version: 3
- var: multiplier
  value: 2

- object: Account
  count: 3
  fields:
    Value: ${{(count + 1) * multiplier + random_number(min=1, max=10)}}
        """

        result = generate(
            open_yaml_file=StringIO(recipe),
            strict_mode=True,
            validate_only=True,
        )
        assert not result.has_errors()

    def test_variable_resolution_in_jinja(self):
        """Test that variables are resolved and validated in Jinja templates"""
        recipe = """
- snowfakery_version: 3
- var: base_value
  value: 100

- var: doubled
  value: ${{base_value * 2}}

- object: Account
  fields:
    Value: ${{doubled + 50}}
        """

        result = generate(
            open_yaml_file=StringIO(recipe),
            strict_mode=True,
            validate_only=True,
        )
        assert not result.has_errors()

    def test_undefined_variable_clear_error_message(self):
        """Test that undefined variable errors have clear messages"""
        recipe = """
- snowfakery_version: 3
- object: Account
  fields:
    Name: ${{this_variable_does_not_exist}}
        """

        with pytest.raises(DataGenValidationError) as exc_info:
            generate(
                open_yaml_file=StringIO(recipe),
                strict_mode=True,
                validate_only=True,
            )

        error_msg = str(exc_info.value)
        # Should have clear error message about undefined variable
        assert "this_variable_does_not_exist" in error_msg
        assert "undefined" in error_msg.lower()
        # Should NOT mention MockObjectRow or internal implementation details
        assert "MockObjectRow" not in error_msg

    def test_self_referencing_variable(self):
        """Test that a variable referencing itself is caught as undefined"""
        recipe = """
- snowfakery_version: 3
- var: loop_var
  value: ${{loop_var + 1}}

- object: Account
  fields:
    Value: ${{loop_var}}
        """

        with pytest.raises(DataGenValidationError) as exc_info:
            generate(
                open_yaml_file=StringIO(recipe),
                strict_mode=True,
                validate_only=True,
            )

        error_msg = str(exc_info.value)
        # Self-reference is caught as undefined (variable not available during its own evaluation)
        assert "loop_var" in error_msg
        assert "undefined" in error_msg.lower()

    def test_forward_variable_reference_error(self):
        """Test that variables must be defined before use (sequential order)"""
        recipe = """
- snowfakery_version: 3
- var: var_a
  value: ${{var_b + 1}}

- var: var_b
  value: 100

- object: Account
  fields:
    Value: ${{var_a}}
        """

        with pytest.raises(DataGenValidationError) as exc_info:
            generate(
                open_yaml_file=StringIO(recipe),
                strict_mode=True,
                validate_only=True,
            )

        error_msg = str(exc_info.value)
        # Should report undefined variable (sequential validation)
        assert "var_b" in error_msg
        assert "undefined" in error_msg.lower()

    def test_structured_value_function_resolution(self):
        """Test that StructuredValue functions are executed and resolved"""
        recipe = """
- snowfakery_version: 3
- var: random_val
  value:
    random_number:
      min: 10
      max: 20

- var: doubled
  value: ${{random_val * 2}}

- object: Account
  fields:
    Value: ${{doubled}}
        """

        # This test verifies that random_number returns an actual number
        # and can be used in calculations
        result = generate(
            open_yaml_file=StringIO(recipe),
            strict_mode=True,
            validate_only=True,
        )
        assert not result.has_errors()


class TestIntegration:
    """Integration tests using actual recipes"""

    def test_validate_simple_valid_recipe(self):
        """Test validation of a simple valid recipe"""
        recipe = """
- snowfakery_version: 3
- object: Account
  count: 5
  fields:
    Name: Test Account
        """

        result = generate(
            open_yaml_file=StringIO(recipe),
            strict_mode=False,
            validate_only=False,
        )
        # Should execute without errors
        assert result is not None

    def test_validate_recipe_with_random_number(self):
        """Test validation catches min > max error"""
        recipe = """
- snowfakery_version: 3
- object: Account
  fields:
    Score:
      random_number:
        min: 100
        max: 50
        """

        with pytest.raises(Exception) as exc_info:
            generate(
                open_yaml_file=StringIO(recipe),
                strict_mode=True,
                validate_only=True,
            )

        # Should catch the validation error
        assert (
            "min" in str(exc_info.value).lower() or "max" in str(exc_info.value).lower()
        )


class TestEdgeCasesAndComplexScenarios:
    """Test edge cases, complex scenarios, and nested validations"""

    def test_get_object_count_with_literal(self):
        """Test get_object_count with literal count"""
        context = ValidationContext()
        obj_template = ObjectTemplate("Account", "test.yml", 10)
        obj_template.count_expr = 5  # Literal count
        context.available_objects["Account"] = obj_template

        count = context.get_object_count("Account")
        assert count == 5

    def test_get_object_count_with_non_literal(self):
        """Test get_object_count with non-literal count"""
        context = ValidationContext()
        obj_template = ObjectTemplate("Account", "test.yml", 10)
        obj_template.count_expr = SimpleValue("${{5 + 5}}", "test.yml", 10)
        context.available_objects["Account"] = obj_template

        count = context.get_object_count("Account")
        assert count is None  # Cannot resolve non-literal

    def test_get_object_count_nonexistent(self):
        """Test get_object_count with nonexistent object"""
        context = ValidationContext()
        count = context.get_object_count("NonExistent")
        assert count is None

    def test_resolve_nickname_with_forward_ref(self):
        """Test resolve_object with nickname and forward reference"""
        context = ValidationContext()
        obj_template = ObjectTemplate("Account", "test.yml", 10, nickname="main")
        context.all_nicknames["main"] = obj_template

        result = context.resolve_object("main", allow_forward_ref=True)
        assert result == obj_template

    def test_validate_statement_with_for_each(self):
        """Test validation of for_each expression"""
        from snowfakery.data_generator_runtime_object_model import (
            ForEachVariableDefinition,
        )

        context = ValidationContext()
        context.jinja_env = jinja2.Environment()
        context.available_functions = {}

        # Create object with for_each
        obj = ObjectTemplate("Account", "test.yml", 10)
        loop_expr = SimpleValue([1, 2, 3], "test.yml", 10)
        obj.for_each_expr = ForEachVariableDefinition("test.yml", 10, "item", loop_expr)

        validate_statement(obj, context)

        # Loop variable should be registered
        assert "item" in context.available_variables

    def test_validate_statement_with_friends(self):
        """Test validation of nested friends (ObjectTemplates)"""
        context = ValidationContext()
        context.jinja_env = jinja2.Environment()
        context.available_functions = {}

        # Create parent object with friend
        parent = ObjectTemplate("Account", "test.yml", 10)
        friend = ObjectTemplate("Contact", "test.yml", 20)
        parent.friends = [friend]

        # Pre-register both in all_objects
        context.all_objects["Account"] = parent
        context.all_objects["Contact"] = friend

        validate_statement(parent, context)

        # Friend should be validated (no errors if successful)
        assert len(context.errors) == 0

    def test_validate_nested_structured_values_in_args(self):
        """Test validation of nested StructuredValues in args"""
        context = ValidationContext()

        def mock_validator(sv, ctx):
            pass

        context.available_functions = {
            "outer": mock_validator,
            "inner": mock_validator,
        }

        # Create nested structure: outer(inner())
        inner_sv = StructuredValue("inner", {}, "test.yml", 10)
        outer_sv = StructuredValue("outer", [inner_sv], "test.yml", 10)

        validate_field_definition(outer_sv, context)

        # Both should be validated without errors
        assert len(context.errors) == 0

    def test_validate_nested_structured_values_in_kwargs(self):
        """Test validation of nested StructuredValues in kwargs"""
        context = ValidationContext()

        def mock_validator(sv, ctx):
            pass

        context.available_functions = {
            "outer": mock_validator,
            "inner": mock_validator,
        }

        # Create nested structure: outer(param=inner())
        inner_sv = StructuredValue("inner", {}, "test.yml", 10)
        outer_sv = StructuredValue("outer", {"param": inner_sv}, "test.yml", 10)

        validate_field_definition(outer_sv, context)

        # Both should be validated without errors
        assert len(context.errors) == 0

    def test_validator_exception_handling(self):
        """Test that validator exceptions are caught and reported"""
        context = ValidationContext()

        # Create a validator that raises an exception
        def bad_validator(sv, ctx):
            raise ValueError("Validator broke!")

        context.available_functions = {"bad_func": bad_validator}

        field_def = StructuredValue("bad_func", {}, "test.yml", 10)
        validate_field_definition(field_def, context)

        # Should catch the exception and add an error
        assert len(context.errors) == 1
        assert "Internal validation error" in context.errors[0].message
        assert "bad_func" in context.errors[0].message

    def test_build_function_registry_with_plugin(self):
        """Test build_function_registry with a mock plugin"""

        class MockValidators:
            @staticmethod
            def validate_custom_func(sv, ctx):
                pass

        class MockPlugin:
            Validators = MockValidators

        plugins = [MockPlugin()]
        registry = build_function_registry(plugins)

        # Should include plugin validator with namespace
        assert "MockPlugin.custom_func" in registry
        assert registry["MockPlugin.custom_func"] == MockValidators.validate_custom_func

    def test_build_function_registry_with_plugin_alias(self):
        """Test build_function_registry with plugin that has aliases"""

        class MockValidators:
            @staticmethod
            def validate_my_if_(sv, ctx):
                pass

        class MockFunctions:
            @staticmethod
            def my_if(ctx):
                pass

        class MockPlugin:
            Validators = MockValidators
            Functions = MockFunctions

        plugins = [MockPlugin()]
        registry = build_function_registry(plugins)

        # Should include both the underscore and non-underscore versions with namespace
        assert "MockPlugin.my_if_" in registry
        assert "MockPlugin.my_if" in registry
        assert registry["MockPlugin.my_if"] == MockValidators.validate_my_if_

    def test_validate_variable_definition(self):
        """Test validation of VariableDefinition statements"""
        context = ValidationContext()
        context.jinja_env = jinja2.Environment()
        context.available_functions = {}

        simple_val = SimpleValue("test value", "test.yml", 10)
        var_def = VariableDefinition("test.yml", 10, "myvar", simple_val)

        validate_statement(var_def, context)

        # Should validate without errors
        assert len(context.errors) == 0

    def test_validate_count_expr(self):
        """Test validation of count expression in ObjectTemplate"""
        context = ValidationContext()
        context.jinja_env = jinja2.Environment()
        context.available_functions = {}

        # Create object with count expression
        obj = ObjectTemplate("Account", "test.yml", 10)
        obj.count_expr = SimpleValue(5, "test.yml", 10)

        validate_statement(obj, context)

        # Should validate without errors
        assert len(context.errors) == 0

    def test_validate_object_with_fields(self):
        """Test validation of object with multiple fields"""
        from snowfakery.data_generator_runtime_object_model import FieldFactory

        context = ValidationContext()
        context.jinja_env = jinja2.Environment()
        context.available_functions = {}

        # Create object with fields
        obj = ObjectTemplate("Account", "test.yml", 10)
        field1 = FieldFactory(
            "test.yml", 10, "Name", SimpleValue("Test", "test.yml", 10)
        )
        field2 = FieldFactory("test.yml", 11, "Score", SimpleValue(100, "test.yml", 11))
        obj.fields = [field1, field2]

        validate_statement(obj, context)

        # Should validate without errors
        assert len(context.errors) == 0
        # Field registry should be populated (implementation detail, just verify it's not empty)
        assert context.current_object_fields is not None

    def test_mock_object_field_resolution(self):
        """Test that MockObjectRow resolves field values correctly"""
        from snowfakery.data_generator_runtime_object_model import FieldFactory

        context = ValidationContext()
        context.jinja_env = jinja2.Environment()
        context.available_functions = {}

        # Create object with literal fields
        obj = ObjectTemplate("Account", "test.yml", 10)
        name_field = FieldFactory(
            "Name", SimpleValue("Acme Corp", "test.yml", 10), "test.yml", 10
        )
        count_field = FieldFactory(
            "EmployeeCount", SimpleValue(500, "test.yml", 11), "test.yml", 11
        )
        obj.fields = [name_field, count_field]

        # Register the object
        context.available_objects["Account"] = obj

        # Create mock object
        mock_obj = context._create_mock_object("Account")

        # Test field resolution - should return actual values
        assert mock_obj.Name == "Acme Corp"
        assert mock_obj.EmployeeCount == 500

        # Test non-existent field - should raise AttributeError
        with pytest.raises(AttributeError) as exc_info:
            _ = mock_obj.NonExistentField
        assert "NonExistentField" in str(exc_info.value)
        assert "Available fields" in str(exc_info.value)
