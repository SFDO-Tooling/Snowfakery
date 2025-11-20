from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from snowfakery.api import generate_data
import snowfakery.data_gen_exceptions as exc
from snowfakery.data_generator_runtime_object_model import StructuredValue
from snowfakery.recipe_validator import ValidationContext
from snowfakery.standard_plugins.Salesforce import Salesforce


class TestSalesforceFunctions:
    """Test Salesforce plugin runtime functionality"""

    def test_contentfile_basic(self, generated_rows):
        """Test basic ContentFile usage"""
        with TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Create test file
            test_file = tmpdir_path / "test.txt"
            test_file.write_text("Test Content", encoding="utf-8")

            # Create recipe in same directory
            recipe_file = tmpdir_path / "recipe.yml"
            recipe_content = """
                - plugin: snowfakery.standard_plugins.Salesforce
                - object: TestObj
                  fields:
                    data:
                      Salesforce.ContentFile: test.txt
            """
            recipe_file.write_text(recipe_content)

            generate_data(str(recipe_file))
            # ContentFile returns base64-encoded content
            data = generated_rows.row_values(0, "data")
            assert data  # Just verify it returns something


class TestSalesforceValidator:
    """Test validators for Salesforce.ProfileId() and Salesforce.ContentFile()"""

    # ========== ProfileId/Profile Tests ==========

    def test_profileid_valid_positional(self):
        """Test valid ProfileId call with positional name"""
        context = ValidationContext()
        sv = StructuredValue(
            "Salesforce.ProfileId", ["System Administrator"], "test.yml", 10
        )

        result = Salesforce.Validators.validate_ProfileId(sv, context)

        assert len(context.errors) == 0
        assert len(context.warnings) == 0
        assert (
            result == "00558000001abcAAA"
        )  # Intelligent mock: Salesforce Profile ID format

    def test_profileid_valid_keyword(self):
        """Test valid ProfileId call with keyword name"""
        context = ValidationContext()
        sv = StructuredValue(
            "Salesforce.ProfileId", {"name": "Standard User"}, "test.yml", 10
        )

        result = Salesforce.Validators.validate_ProfileId(sv, context)

        assert len(context.errors) == 0
        assert len(context.warnings) == 0
        assert (
            result == "00558000001abcAAA"
        )  # Intelligent mock: Salesforce Profile ID format

    def test_profile_alias(self):
        """Test that Profile is an alias for ProfileId"""
        context = ValidationContext()
        sv = StructuredValue(
            "Salesforce.Profile", {"name": "Marketing User"}, "test.yml", 10
        )

        result = Salesforce.Validators.validate_Profile(sv, context)

        assert len(context.errors) == 0
        assert (
            result == "00558000001abcAAA"
        )  # Intelligent mock: Salesforce Profile ID format

    def test_profileid_missing_name(self):
        """Test error when name parameter is missing"""
        context = ValidationContext()
        sv = StructuredValue("Salesforce.ProfileId", {}, "test.yml", 10)

        Salesforce.Validators.validate_ProfileId(sv, context)

        assert len(context.errors) >= 1
        assert any(
            "missing" in err.message.lower() and "name" in err.message.lower()
            for err in context.errors
        )

    def test_profileid_invalid_type(self):
        """Test error when name is not a string"""
        context = ValidationContext()
        sv = StructuredValue("Salesforce.ProfileId", {"name": 123}, "test.yml", 10)

        Salesforce.Validators.validate_ProfileId(sv, context)

        assert len(context.errors) >= 1
        assert any(
            "name" in err.message.lower() and "string" in err.message.lower()
            for err in context.errors
        )

    def test_profileid_invalid_type_list(self):
        """Test error when name is a list"""
        context = ValidationContext()
        sv = StructuredValue(
            "Salesforce.ProfileId", {"name": ["Admin"]}, "test.yml", 10
        )

        Salesforce.Validators.validate_ProfileId(sv, context)

        assert len(context.errors) >= 1
        assert any("name" in err.message.lower() for err in context.errors)

    def test_profileid_multiple_positional_args(self):
        """Test error when multiple positional args provided"""
        context = ValidationContext()
        sv = StructuredValue("Salesforce.ProfileId", ["Admin", "Extra"], "test.yml", 10)

        Salesforce.Validators.validate_ProfileId(sv, context)

        assert len(context.errors) >= 1
        assert any("1 positional argument" in err.message for err in context.errors)

    def test_profileid_unknown_parameters(self):
        """Test warning for unknown parameters"""
        context = ValidationContext()
        sv = StructuredValue(
            "Salesforce.ProfileId",
            {"name": "System Administrator", "unknown_param": "value"},
            "test.yml",
            10,
        )

        Salesforce.Validators.validate_ProfileId(sv, context)

        assert len(context.warnings) >= 1
        assert any(
            "unknown parameter" in warn.message.lower() for warn in context.warnings
        )

    # ========== ContentFile Tests ==========

    def test_contentfile_valid_positional(self):
        """Test valid ContentFile call with positional file"""
        with TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            test_file = tmpdir_path / "test.txt"
            test_file.write_text("Test", encoding="utf-8")

            recipe_file = tmpdir_path / "recipe.yml"

            context = ValidationContext()
            context.current_template = type(
                "obj", (object,), {"filename": str(recipe_file)}
            )()

            sv = StructuredValue(
                "Salesforce.ContentFile", ["test.txt"], str(recipe_file), 10
            )

            result = Salesforce.Validators.validate_ContentFile(sv, context)

            assert len(context.errors) == 0
            assert len(context.warnings) == 0
            # Intelligent mock: base64-encoded "Mock file content for validation"
            assert result == "TW9jayBmaWxlIGNvbnRlbnQgZm9yIHZhbGlkYXRpb24="

    def test_contentfile_valid_keyword(self):
        """Test valid ContentFile call with keyword file"""
        with TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            test_file = tmpdir_path / "test.txt"
            test_file.write_text("Test", encoding="utf-8")

            recipe_file = tmpdir_path / "recipe.yml"

            context = ValidationContext()
            context.current_template = type(
                "obj", (object,), {"filename": str(recipe_file)}
            )()

            sv = StructuredValue(
                "Salesforce.ContentFile", {"file": "test.txt"}, str(recipe_file), 10
            )

            result = Salesforce.Validators.validate_ContentFile(sv, context)

            assert len(context.errors) == 0
            assert len(context.warnings) == 0
            # Intelligent mock: base64-encoded "Mock file content for validation"
            assert result == "TW9jayBmaWxlIGNvbnRlbnQgZm9yIHZhbGlkYXRpb24="

    def test_contentfile_missing_file(self):
        """Test error when file parameter is missing"""
        context = ValidationContext()
        sv = StructuredValue("Salesforce.ContentFile", {}, "test.yml", 10)

        Salesforce.Validators.validate_ContentFile(sv, context)

        assert len(context.errors) >= 1
        assert any(
            "missing" in err.message.lower() and "file" in err.message.lower()
            for err in context.errors
        )

    def test_contentfile_invalid_type(self):
        """Test error when file is not a string"""
        context = ValidationContext()
        sv = StructuredValue("Salesforce.ContentFile", {"file": 123}, "test.yml", 10)

        Salesforce.Validators.validate_ContentFile(sv, context)

        assert len(context.errors) >= 1
        assert any(
            "file" in err.message.lower() and "string" in err.message.lower()
            for err in context.errors
        )

    def test_contentfile_invalid_type_list(self):
        """Test error when file is a list"""
        context = ValidationContext()
        sv = StructuredValue(
            "Salesforce.ContentFile", {"file": ["test.txt"]}, "test.yml", 10
        )

        Salesforce.Validators.validate_ContentFile(sv, context)

        assert len(context.errors) >= 1
        assert any("file" in err.message.lower() for err in context.errors)

    def test_contentfile_file_not_exists(self):
        """Test error when file doesn't exist"""
        with TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            recipe_file = tmpdir_path / "recipe.yml"

            context = ValidationContext()
            context.current_template = type(
                "obj", (object,), {"filename": str(recipe_file)}
            )()

            sv = StructuredValue(
                "Salesforce.ContentFile",
                {"file": "nonexistent.txt"},
                str(recipe_file),
                10,
            )

            Salesforce.Validators.validate_ContentFile(sv, context)

            assert len(context.errors) >= 1
            assert any("not found" in err.message.lower() for err in context.errors)

    def test_contentfile_path_is_directory(self):
        """Test error when path is a directory"""
        with TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            test_dir = tmpdir_path / "testdir"
            test_dir.mkdir()

            recipe_file = tmpdir_path / "recipe.yml"

            context = ValidationContext()
            context.current_template = type(
                "obj", (object,), {"filename": str(recipe_file)}
            )()

            sv = StructuredValue(
                "Salesforce.ContentFile", {"file": "testdir"}, str(recipe_file), 10
            )

            Salesforce.Validators.validate_ContentFile(sv, context)

            assert len(context.errors) >= 1
            assert any(
                "directory" in err.message.lower()
                or "not a file" in err.message.lower()
                for err in context.errors
            )

    def test_contentfile_multiple_positional_args(self):
        """Test error when multiple positional args provided"""
        context = ValidationContext()
        sv = StructuredValue(
            "Salesforce.ContentFile", ["file1.txt", "file2.txt"], "test.yml", 10
        )

        Salesforce.Validators.validate_ContentFile(sv, context)

        assert len(context.errors) >= 1
        assert any("1 positional argument" in err.message for err in context.errors)

    def test_contentfile_unknown_parameters(self):
        """Test warning for unknown parameters"""
        with TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            test_file = tmpdir_path / "test.txt"
            test_file.write_text("Test", encoding="utf-8")

            recipe_file = tmpdir_path / "recipe.yml"

            context = ValidationContext()
            context.current_template = type(
                "obj", (object,), {"filename": str(recipe_file)}
            )()

            sv = StructuredValue(
                "Salesforce.ContentFile",
                {"file": "test.txt", "unknown_param": "value"},
                str(recipe_file),
                10,
            )

            Salesforce.Validators.validate_ContentFile(sv, context)

            assert len(context.warnings) >= 1
            assert any(
                "unknown parameter" in warn.message.lower() for warn in context.warnings
            )


class TestSalesforceValidationIntegration:
    """Integration tests for Salesforce validation"""

    def test_profileid_in_recipe_valid(self):
        """Test valid ProfileId in recipe"""
        yaml = """
        - plugin: snowfakery.standard_plugins.Salesforce
        - object: User
          fields:
            ProfileId:
              Salesforce.ProfileId: System Administrator
        """
        result = generate_data(StringIO(yaml), validate_only=True)
        assert result.errors == []

    def test_profileid_in_recipe_invalid(self):
        """Test invalid ProfileId in recipe"""
        yaml = """
        - plugin: snowfakery.standard_plugins.Salesforce
        - object: User
          fields:
            ProfileId:
              Salesforce.ProfileId: 123
        """
        with pytest.raises(exc.DataGenValidationError) as e:
            generate_data(StringIO(yaml), validate_only=True)
        assert "profileid" in str(e.value).lower() or "name" in str(e.value).lower()

    def test_profile_alias_in_recipe(self):
        """Test Profile alias in recipe"""
        yaml = """
        - plugin: snowfakery.standard_plugins.Salesforce
        - object: User
          fields:
            ProfileId:
              Salesforce.Profile: Standard User
        """
        result = generate_data(StringIO(yaml), validate_only=True)
        assert result.errors == []

    def test_contentfile_in_recipe_valid(self):
        """Test valid ContentFile in recipe"""
        with TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            test_file = tmpdir_path / "test.txt"
            test_file.write_text("Test Content", encoding="utf-8")

            recipe_file = tmpdir_path / "recipe.yml"
            recipe_content = """
                - plugin: snowfakery.standard_plugins.Salesforce
                - object: ContentVersion
                  fields:
                    VersionData:
                      Salesforce.ContentFile: test.txt
            """
            recipe_file.write_text(recipe_content)

            result = generate_data(str(recipe_file), validate_only=True)
            assert result.errors == []

    def test_contentfile_in_recipe_invalid_missing_file(self):
        """Test ContentFile with missing file in recipe"""
        with TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            recipe_file = tmpdir_path / "recipe.yml"
            recipe_content = """
                - plugin: snowfakery.standard_plugins.Salesforce
                - object: ContentVersion
                  fields:
                    VersionData:
                      Salesforce.ContentFile: nonexistent.txt
            """
            recipe_file.write_text(recipe_content)

            with pytest.raises(exc.DataGenValidationError) as e:
                generate_data(str(recipe_file), validate_only=True)
            assert (
                "not found" in str(e.value).lower()
                or "contentfile" in str(e.value).lower()
            )
