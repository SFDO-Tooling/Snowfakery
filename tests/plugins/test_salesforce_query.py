from io import StringIO

import pytest

from snowfakery.api import generate_data
import snowfakery.data_gen_exceptions as exc
from snowfakery.data_generator_runtime_object_model import StructuredValue
from snowfakery.recipe_validator import ValidationContext
from snowfakery.standard_plugins.Salesforce import SalesforceQuery


class TestSalesforceQueryValidator:
    """Test validators for SalesforceQuery.random_record() and SalesforceQuery.find_record()"""

    # ========== random_record Tests ==========

    def test_random_record_valid_positional(self):
        """Test valid random_record call with positional from"""
        context = ValidationContext()
        sv = StructuredValue(
            "SalesforceQuery.random_record", ["Account"], "test.yml", 10
        )

        result = SalesforceQuery.Validators.validate_random_record(sv, context)

        assert len(context.errors) == 0
        assert len(context.warnings) == 0
        assert result is not None
        assert hasattr(result, "Id")

    def test_random_record_valid_keyword(self):
        """Test valid random_record call with keyword from"""
        context = ValidationContext()
        sv = StructuredValue(
            "SalesforceQuery.random_record", {"from": "Contact"}, "test.yml", 10
        )

        result = SalesforceQuery.Validators.validate_random_record(sv, context)

        assert len(context.errors) == 0
        assert len(context.warnings) == 0
        assert result is not None
        assert hasattr(result, "Id")

    def test_random_record_with_fields(self):
        """Test random_record with multiple fields"""
        context = ValidationContext()
        sv = StructuredValue(
            "SalesforceQuery.random_record",
            {"from": "Account", "fields": "Id, Name, Email"},
            "test.yml",
            10,
        )

        result = SalesforceQuery.Validators.validate_random_record(sv, context)

        assert len(context.errors) == 0
        assert hasattr(result, "Id")
        assert hasattr(result, "Name")
        assert hasattr(result, "Email")

    def test_random_record_with_where(self):
        """Test random_record with WHERE clause"""
        context = ValidationContext()
        sv = StructuredValue(
            "SalesforceQuery.random_record",
            {"from": "Opportunity", "where": "StageName = 'Closed Won'"},
            "test.yml",
            10,
        )

        SalesforceQuery.Validators.validate_random_record(sv, context)

        assert len(context.errors) == 0
        assert len(context.warnings) == 0

    def test_random_record_missing_from(self):
        """Test error when from parameter is missing"""
        context = ValidationContext()
        sv = StructuredValue(
            "SalesforceQuery.random_record", {"fields": "Id, Name"}, "test.yml", 10
        )

        SalesforceQuery.Validators.validate_random_record(sv, context)

        assert len(context.errors) >= 1
        assert any(
            "missing" in err.message.lower() and "from" in err.message.lower()
            for err in context.errors
        )

    def test_random_record_from_invalid_type(self):
        """Test error when from is not a string"""
        context = ValidationContext()
        sv = StructuredValue(
            "SalesforceQuery.random_record", {"from": 123}, "test.yml", 10
        )

        SalesforceQuery.Validators.validate_random_record(sv, context)

        assert len(context.errors) >= 1
        assert any(
            "from" in err.message.lower() and "string" in err.message.lower()
            for err in context.errors
        )

    def test_random_record_from_invalid_type_list(self):
        """Test error when from is a list"""
        context = ValidationContext()
        sv = StructuredValue(
            "SalesforceQuery.random_record", {"from": ["Account"]}, "test.yml", 10
        )

        SalesforceQuery.Validators.validate_random_record(sv, context)

        assert len(context.errors) >= 1
        assert any("from" in err.message.lower() for err in context.errors)

    def test_random_record_fields_invalid_type(self):
        """Test error when fields is not a string"""
        context = ValidationContext()
        sv = StructuredValue(
            "SalesforceQuery.random_record",
            {"from": "Account", "fields": 123},
            "test.yml",
            10,
        )

        SalesforceQuery.Validators.validate_random_record(sv, context)

        assert len(context.errors) >= 1
        assert any(
            "fields" in err.message.lower() and "string" in err.message.lower()
            for err in context.errors
        )

    def test_random_record_fields_invalid_type_list(self):
        """Test error when fields is a list"""
        context = ValidationContext()
        sv = StructuredValue(
            "SalesforceQuery.random_record",
            {"from": "Account", "fields": ["Id", "Name"]},
            "test.yml",
            10,
        )

        SalesforceQuery.Validators.validate_random_record(sv, context)

        assert len(context.errors) >= 1
        assert any("fields" in err.message.lower() for err in context.errors)

    def test_random_record_where_invalid_type(self):
        """Test error when where is not a string"""
        context = ValidationContext()
        sv = StructuredValue(
            "SalesforceQuery.random_record",
            {"from": "Account", "where": 123},
            "test.yml",
            10,
        )

        SalesforceQuery.Validators.validate_random_record(sv, context)

        assert len(context.errors) >= 1
        assert any(
            "where" in err.message.lower() and "string" in err.message.lower()
            for err in context.errors
        )

    def test_random_record_multiple_positional_args(self):
        """Test error when multiple positional args provided"""
        context = ValidationContext()
        sv = StructuredValue(
            "SalesforceQuery.random_record", ["Account", "Contact"], "test.yml", 10
        )

        SalesforceQuery.Validators.validate_random_record(sv, context)

        assert len(context.errors) >= 1
        assert any("1 positional argument" in err.message for err in context.errors)

    def test_random_record_both_positional_and_keyword_from(self):
        """Test warning when from specified both ways"""
        context = ValidationContext()
        # Create StructuredValue with both args and kwargs
        sv = StructuredValue(
            "SalesforceQuery.random_record", ["Account"], "test.yml", 10
        )
        sv.kwargs = {"from": "Contact"}  # Add keyword arg manually

        SalesforceQuery.Validators.validate_random_record(sv, context)

        assert len(context.warnings) >= 1
        assert any(
            "both" in warn.message.lower() and "from" in warn.message.lower()
            for warn in context.warnings
        )

    def test_random_record_unknown_parameters(self):
        """Test warning for unknown parameters"""
        context = ValidationContext()
        sv = StructuredValue(
            "SalesforceQuery.random_record",
            {"from": "Account", "unknown_param": "value"},
            "test.yml",
            10,
        )

        SalesforceQuery.Validators.validate_random_record(sv, context)

        assert len(context.warnings) >= 1
        assert any(
            "unknown parameter" in warn.message.lower() for warn in context.warnings
        )

    def test_random_record_mock_object_has_fields(self):
        """Test that mock object has correct field attributes"""
        context = ValidationContext()
        sv = StructuredValue(
            "SalesforceQuery.random_record",
            {"from": "Account", "fields": "Id, Name, Industry"},
            "test.yml",
            10,
        )

        result = SalesforceQuery.Validators.validate_random_record(sv, context)

        assert hasattr(result, "Id")
        assert hasattr(result, "Name")
        assert hasattr(result, "Industry")
        assert result.Id == "<mock_Id>"
        assert result.Name == "<mock_Name>"
        assert result.Industry == "<mock_Industry>"

    # ========== find_record Tests ==========

    def test_find_record_valid_positional(self):
        """Test valid find_record call with positional from"""
        context = ValidationContext()
        sv = StructuredValue("SalesforceQuery.find_record", ["Account"], "test.yml", 10)

        result = SalesforceQuery.Validators.validate_find_record(sv, context)

        assert len(context.errors) == 0
        assert len(context.warnings) == 0
        assert result is not None
        assert hasattr(result, "Id")

    def test_find_record_valid_keyword(self):
        """Test valid find_record call with keyword from"""
        context = ValidationContext()
        sv = StructuredValue(
            "SalesforceQuery.find_record", {"from": "Contact"}, "test.yml", 10
        )

        result = SalesforceQuery.Validators.validate_find_record(sv, context)

        assert len(context.errors) == 0
        assert len(context.warnings) == 0
        assert result is not None
        assert hasattr(result, "Id")

    def test_find_record_with_fields(self):
        """Test find_record with multiple fields"""
        context = ValidationContext()
        sv = StructuredValue(
            "SalesforceQuery.find_record",
            {"from": "Account", "fields": "Id, Name, Email"},
            "test.yml",
            10,
        )

        result = SalesforceQuery.Validators.validate_find_record(sv, context)

        assert len(context.errors) == 0
        assert hasattr(result, "Id")
        assert hasattr(result, "Name")
        assert hasattr(result, "Email")

    def test_find_record_with_where(self):
        """Test find_record with WHERE clause"""
        context = ValidationContext()
        sv = StructuredValue(
            "SalesforceQuery.find_record",
            {"from": "Account", "where": "Name = 'Acme Corp'"},
            "test.yml",
            10,
        )

        SalesforceQuery.Validators.validate_find_record(sv, context)

        assert len(context.errors) == 0
        assert len(context.warnings) == 0

    def test_find_record_missing_from(self):
        """Test error when from parameter is missing"""
        context = ValidationContext()
        sv = StructuredValue(
            "SalesforceQuery.find_record", {"fields": "Id, Name"}, "test.yml", 10
        )

        SalesforceQuery.Validators.validate_find_record(sv, context)

        assert len(context.errors) >= 1
        assert any(
            "missing" in err.message.lower() and "from" in err.message.lower()
            for err in context.errors
        )

    def test_find_record_from_invalid_type(self):
        """Test error when from is not a string"""
        context = ValidationContext()
        sv = StructuredValue(
            "SalesforceQuery.find_record", {"from": 123}, "test.yml", 10
        )

        SalesforceQuery.Validators.validate_find_record(sv, context)

        assert len(context.errors) >= 1
        assert any(
            "from" in err.message.lower() and "string" in err.message.lower()
            for err in context.errors
        )

    def test_find_record_from_invalid_type_list(self):
        """Test error when from is a list"""
        context = ValidationContext()
        sv = StructuredValue(
            "SalesforceQuery.find_record", {"from": ["Account"]}, "test.yml", 10
        )

        SalesforceQuery.Validators.validate_find_record(sv, context)

        assert len(context.errors) >= 1
        assert any("from" in err.message.lower() for err in context.errors)

    def test_find_record_fields_invalid_type(self):
        """Test error when fields is not a string"""
        context = ValidationContext()
        sv = StructuredValue(
            "SalesforceQuery.find_record",
            {"from": "Account", "fields": 123},
            "test.yml",
            10,
        )

        SalesforceQuery.Validators.validate_find_record(sv, context)

        assert len(context.errors) >= 1
        assert any(
            "fields" in err.message.lower() and "string" in err.message.lower()
            for err in context.errors
        )

    def test_find_record_fields_invalid_type_list(self):
        """Test error when fields is a list"""
        context = ValidationContext()
        sv = StructuredValue(
            "SalesforceQuery.find_record",
            {"from": "Account", "fields": ["Id", "Name"]},
            "test.yml",
            10,
        )

        SalesforceQuery.Validators.validate_find_record(sv, context)

        assert len(context.errors) >= 1
        assert any("fields" in err.message.lower() for err in context.errors)

    def test_find_record_where_invalid_type(self):
        """Test error when where is not a string"""
        context = ValidationContext()
        sv = StructuredValue(
            "SalesforceQuery.find_record",
            {"from": "Account", "where": 123},
            "test.yml",
            10,
        )

        SalesforceQuery.Validators.validate_find_record(sv, context)

        assert len(context.errors) >= 1
        assert any(
            "where" in err.message.lower() and "string" in err.message.lower()
            for err in context.errors
        )

    def test_find_record_multiple_positional_args(self):
        """Test error when multiple positional args provided"""
        context = ValidationContext()
        sv = StructuredValue(
            "SalesforceQuery.find_record", ["Account", "Contact"], "test.yml", 10
        )

        SalesforceQuery.Validators.validate_find_record(sv, context)

        assert len(context.errors) >= 1
        assert any("1 positional argument" in err.message for err in context.errors)

    def test_find_record_both_positional_and_keyword_from(self):
        """Test warning when from specified both ways"""
        context = ValidationContext()
        # Create StructuredValue with both args and kwargs
        sv = StructuredValue("SalesforceQuery.find_record", ["Account"], "test.yml", 10)
        sv.kwargs = {"from": "Contact"}  # Add keyword arg manually

        SalesforceQuery.Validators.validate_find_record(sv, context)

        assert len(context.warnings) >= 1
        assert any(
            "both" in warn.message.lower() and "from" in warn.message.lower()
            for warn in context.warnings
        )

    def test_find_record_unknown_parameters(self):
        """Test warning for unknown parameters"""
        context = ValidationContext()
        sv = StructuredValue(
            "SalesforceQuery.find_record",
            {"from": "Account", "unknown_param": "value"},
            "test.yml",
            10,
        )

        SalesforceQuery.Validators.validate_find_record(sv, context)

        assert len(context.warnings) >= 1
        assert any(
            "unknown parameter" in warn.message.lower() for warn in context.warnings
        )

    def test_find_record_mock_object_has_fields(self):
        """Test that mock object has correct field attributes"""
        context = ValidationContext()
        sv = StructuredValue(
            "SalesforceQuery.find_record",
            {"from": "Account", "fields": "Id, Name, Industry"},
            "test.yml",
            10,
        )

        result = SalesforceQuery.Validators.validate_find_record(sv, context)

        assert hasattr(result, "Id")
        assert hasattr(result, "Name")
        assert hasattr(result, "Industry")
        assert result.Id == "<mock_Id>"
        assert result.Name == "<mock_Name>"
        assert result.Industry == "<mock_Industry>"


class TestSalesforceQueryValidationIntegration:
    """Integration tests for SalesforceQuery validation"""

    def test_random_record_in_recipe_valid(self):
        """Test valid random_record in recipe"""
        yaml = """
        - plugin: snowfakery.standard_plugins.Salesforce.SalesforceQuery
        - object: TestObj
          fields:
            AccountId:
              SalesforceQuery.random_record: Account
        """
        result = generate_data(StringIO(yaml), validate_only=True)
        assert result.errors == []

    def test_random_record_in_recipe_invalid(self):
        """Test invalid random_record in recipe"""
        yaml = """
        - plugin: snowfakery.standard_plugins.Salesforce.SalesforceQuery
        - object: TestObj
          fields:
            AccountId:
              SalesforceQuery.random_record:
                fields: Id, Name
        """
        with pytest.raises(exc.DataGenValidationError) as e:
            generate_data(StringIO(yaml), validate_only=True)
        assert "from" in str(e.value).lower()

    def test_find_record_in_recipe_valid(self):
        """Test valid find_record in recipe"""
        yaml = """
        - plugin: snowfakery.standard_plugins.Salesforce.SalesforceQuery
        - object: TestObj
          fields:
            ContactId:
              SalesforceQuery.find_record:
                from: Contact
                fields: Id, Name
        """
        result = generate_data(StringIO(yaml), validate_only=True)
        assert result.errors == []

    def test_find_record_in_recipe_invalid(self):
        """Test invalid find_record in recipe"""
        yaml = """
        - plugin: snowfakery.standard_plugins.Salesforce.SalesforceQuery
        - object: TestObj
          fields:
            ContactId:
              SalesforceQuery.find_record:
                from: 123
        """
        with pytest.raises(exc.DataGenValidationError) as e:
            generate_data(StringIO(yaml), validate_only=True)
        assert "from" in str(e.value).lower() or "string" in str(e.value).lower()

    def test_mock_object_field_access(self):
        """Test accessing mock object fields in recipe"""
        yaml = """
        - plugin: snowfakery.standard_plugins.Salesforce.SalesforceQuery
        - var: account
          value:
            SalesforceQuery.random_record:
              from: Account
              fields: Id, Name, Industry
        - object: TestObj
          fields:
            # These should validate without errors
            AccountName: ${{account.Name}}
            AccountId: ${{account.Id}}
        """
        result = generate_data(StringIO(yaml), validate_only=True)
        assert result.errors == []
