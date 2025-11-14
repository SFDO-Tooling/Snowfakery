from pathlib import Path
from tempfile import TemporaryDirectory

from snowfakery.api import generate_data
from snowfakery.data_generator_runtime_object_model import StructuredValue
from snowfakery.recipe_validator import ValidationContext
from snowfakery.standard_plugins.file import File


class TestFileFunctions:
    """Test File plugin runtime functionality."""

    def test_file_data_basic(self, generated_rows):
        """Test basic file reading with default UTF-8 encoding"""
        with TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Create test file
            test_file = tmpdir_path / "test_data.txt"
            test_file.write_text("Hello World", encoding="utf-8")

            # Create recipe in same directory
            recipe_file = tmpdir_path / "recipe.yml"
            recipe_content = """
                - plugin: snowfakery.standard_plugins.file.File
                - object: Example
                  fields:
                    data:
                      File.file_data: test_data.txt
            """
            recipe_file.write_text(recipe_content)

            generate_data(str(recipe_file))
            data = generated_rows.row_values(0, "data")
            assert data == "Hello World"

    def test_file_data_with_keyword_arg(self, generated_rows):
        """Test file reading with keyword argument"""
        with TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Create test file
            test_file = tmpdir_path / "test_data.txt"
            test_file.write_text("Test Content", encoding="utf-8")

            # Create recipe
            recipe_file = tmpdir_path / "recipe.yml"
            recipe_content = """
                - plugin: snowfakery.standard_plugins.file.File
                - object: Example
                  fields:
                    data:
                      File.file_data:
                        file: test_data.txt
            """
            recipe_file.write_text(recipe_content)

            generate_data(str(recipe_file))
            data = generated_rows.row_values(0, "data")
            assert data == "Test Content"

    def test_file_data_with_encoding(self, generated_rows):
        """Test file reading with specific encoding"""
        with TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Create test file with latin-1 encoding
            test_file = tmpdir_path / "test_data.txt"
            test_file.write_text("Café", encoding="latin-1")

            # Create recipe
            recipe_file = tmpdir_path / "recipe.yml"
            recipe_content = """
                - plugin: snowfakery.standard_plugins.file.File
                - object: Example
                  fields:
                    data:
                      File.file_data:
                        file: test_data.txt
                        encoding: latin-1
            """
            recipe_file.write_text(recipe_content)

            generate_data(str(recipe_file))
            data = generated_rows.row_values(0, "data")
            assert data == "Café"

    def test_file_data_binary_encoding(self, generated_rows):
        """Test file reading with binary encoding"""
        with TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Create binary test file
            test_file = tmpdir_path / "test_data.bin"
            test_file.write_bytes(b"\x00\x01\x02\x03")

            # Create recipe
            recipe_file = tmpdir_path / "recipe.yml"
            recipe_content = """
                - plugin: snowfakery.standard_plugins.file.File
                - object: Example
                  fields:
                    data:
                      File.file_data:
                        file: test_data.bin
                        encoding: binary
            """
            recipe_file.write_text(recipe_content)

            generate_data(str(recipe_file))
            data = generated_rows.row_values(0, "data")
            # Binary encoding uses latin-1 internally
            assert data == "\x00\x01\x02\x03"


class TestFileValidator:
    """Test validators for File.file_data()"""

    def test_valid_positional_arg(self):
        """Test valid call with positional argument"""
        with TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            test_file = tmpdir_path / "test.txt"
            test_file.write_text("content")

            recipe_file = tmpdir_path / "recipe.yml"

            context = ValidationContext()
            context.current_template = type(
                "obj", (object,), {"filename": str(recipe_file)}
            )()

            sv = StructuredValue("File.file_data", ["test.txt"], "recipe.yml", 10)
            File.Validators.validate_file_data(sv, context)

            assert len(context.errors) == 0
            assert len(context.warnings) == 0

    def test_valid_keyword_arg(self):
        """Test valid call with keyword argument"""
        with TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            test_file = tmpdir_path / "test.txt"
            test_file.write_text("content")

            recipe_file = tmpdir_path / "recipe.yml"

            context = ValidationContext()
            context.current_template = type(
                "obj", (object,), {"filename": str(recipe_file)}
            )()

            sv = StructuredValue(
                "File.file_data", {"file": "test.txt"}, "recipe.yml", 10
            )
            File.Validators.validate_file_data(sv, context)

            assert len(context.errors) == 0
            assert len(context.warnings) == 0

    def test_valid_with_encoding(self):
        """Test valid call with encoding parameter"""
        with TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            test_file = tmpdir_path / "test.txt"
            test_file.write_text("content")

            recipe_file = tmpdir_path / "recipe.yml"

            context = ValidationContext()
            context.current_template = type(
                "obj", (object,), {"filename": str(recipe_file)}
            )()

            sv = StructuredValue(
                "File.file_data",
                {"file": "test.txt", "encoding": "utf-8"},
                "recipe.yml",
                10,
            )
            File.Validators.validate_file_data(sv, context)

            assert len(context.errors) == 0
            assert len(context.warnings) == 0

    def test_missing_file_parameter(self):
        """Test error when file parameter is missing"""
        context = ValidationContext()
        sv = StructuredValue("File.file_data", {}, "test.yml", 10)

        File.Validators.validate_file_data(sv, context)

        assert len(context.errors) >= 1
        assert any(
            "missing required parameter" in err.message.lower()
            and "file" in err.message.lower()
            for err in context.errors
        )

    def test_file_not_exists(self):
        """Test error when file does not exist"""
        with TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            recipe_file = tmpdir_path / "recipe.yml"

            context = ValidationContext()
            context.current_template = type(
                "obj", (object,), {"filename": str(recipe_file)}
            )()

            sv = StructuredValue(
                "File.file_data", ["nonexistent.txt"], "recipe.yml", 10
            )
            File.Validators.validate_file_data(sv, context)

            assert len(context.errors) >= 1
            assert any(
                "does not exist" in err.message.lower() for err in context.errors
            )

    def test_file_must_be_string(self):
        """Test error when file parameter is not a string"""
        context = ValidationContext()
        sv = StructuredValue("File.file_data", {"file": 123}, "test.yml", 10)

        File.Validators.validate_file_data(sv, context)

        assert len(context.errors) >= 1
        assert any(
            "must be a string" in err.message.lower() and "file" in err.message.lower()
            for err in context.errors
        )

    def test_encoding_must_be_string(self):
        """Test error when encoding parameter is not a string"""
        with TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            test_file = tmpdir_path / "test.txt"
            test_file.write_text("content")

            recipe_file = tmpdir_path / "recipe.yml"

            context = ValidationContext()
            context.current_template = type(
                "obj", (object,), {"filename": str(recipe_file)}
            )()

            sv = StructuredValue(
                "File.file_data",
                {"file": "test.txt", "encoding": 123},
                "recipe.yml",
                10,
            )
            File.Validators.validate_file_data(sv, context)

            assert len(context.errors) >= 1
            assert any(
                "must be a string" in err.message.lower()
                and "encoding" in err.message.lower()
                for err in context.errors
            )

    def test_unknown_parameter(self):
        """Test warning for unknown parameters"""
        with TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            test_file = tmpdir_path / "test.txt"
            test_file.write_text("content")

            recipe_file = tmpdir_path / "recipe.yml"

            context = ValidationContext()
            context.current_template = type(
                "obj", (object,), {"filename": str(recipe_file)}
            )()

            sv = StructuredValue(
                "File.file_data",
                {"file": "test.txt", "mode": "rb"},
                "recipe.yml",
                10,
            )
            File.Validators.validate_file_data(sv, context)

            assert len(context.errors) == 0
            assert len(context.warnings) >= 1
            assert any(
                "unknown parameter" in warn.message.lower()
                and "mode" in warn.message.lower()
                for warn in context.warnings
            )

    def test_path_is_not_file(self):
        """Test error when path exists but is not a file (e.g., directory)"""
        with TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            # Create a subdirectory
            subdir = tmpdir_path / "subdir"
            subdir.mkdir()

            recipe_file = tmpdir_path / "recipe.yml"

            context = ValidationContext()
            context.current_template = type(
                "obj", (object,), {"filename": str(recipe_file)}
            )()

            sv = StructuredValue("File.file_data", ["subdir"], "recipe.yml", 10)
            File.Validators.validate_file_data(sv, context)

            assert len(context.errors) >= 1
            assert any("is not a file" in err.message.lower() for err in context.errors)
