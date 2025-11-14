from pathlib import Path
from tempfile import TemporaryDirectory

from snowfakery.api import generate_data
from snowfakery.data_generator_runtime_object_model import StructuredValue
from snowfakery.recipe_validator import ValidationContext
from snowfakery.standard_plugins.datasets import Dataset


class TestDatasetFunctions:
    """Test Dataset plugin runtime functionality."""

    def test_iterate_csv_basic(self, generated_rows):
        """Test basic CSV iteration"""
        with TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Create test CSV file
            csv_file = tmpdir_path / "users.csv"
            csv_file.write_text("FirstName,LastName\nJohn,Doe\nJane,Smith\n")

            # Create recipe
            recipe_file = tmpdir_path / "recipe.yml"
            recipe_content = """
                - plugin: snowfakery.standard_plugins.datasets.Dataset
                - object: User
                  count: 2
                  fields:
                    __user_from_csv:
                      Dataset.iterate:
                        dataset: users.csv
                    first: ${{__user_from_csv.FirstName}}
                    last: ${{__user_from_csv.LastName}}
            """
            recipe_file.write_text(recipe_content)

            generate_data(str(recipe_file))
            assert generated_rows.row_values(0, "first") == "John"
            assert generated_rows.row_values(0, "last") == "Doe"
            assert generated_rows.row_values(1, "first") == "Jane"
            assert generated_rows.row_values(1, "last") == "Smith"

    def test_shuffle_csv_basic(self, generated_rows):
        """Test basic CSV shuffle"""
        with TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Create test CSV file
            csv_file = tmpdir_path / "data.csv"
            csv_file.write_text("Value\nA\nB\nC\n")

            # Create recipe
            recipe_file = tmpdir_path / "recipe.yml"
            recipe_content = """
                - plugin: snowfakery.standard_plugins.datasets.Dataset
                - object: Item
                  count: 3
                  fields:
                    __data_from_csv:
                      Dataset.shuffle:
                        dataset: data.csv
                    value: ${{__data_from_csv.Value}}
            """
            recipe_file.write_text(recipe_content)

            generate_data(str(recipe_file))
            # Just verify it runs without error; actual shuffle order is random
            # Verify we got 3 rows with values from the CSV
            values = [generated_rows.row_values(i, "value") for i in range(3)]
            assert all(v in ["A", "B", "C"] for v in values)


class TestDatasetValidator:
    """Test validators for Dataset.iterate() and Dataset.shuffle()"""

    def test_iterate_valid_csv(self):
        """Test valid CSV dataset with iterate"""
        with TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            csv_file = tmpdir_path / "data.csv"
            csv_file.write_text("col1,col2\nval1,val2\n")

            recipe_file = tmpdir_path / "recipe.yml"

            context = ValidationContext()
            context.current_template = type(
                "obj", (object,), {"filename": str(recipe_file)}
            )()

            sv = StructuredValue(
                "Dataset.iterate", {"dataset": "data.csv"}, "recipe.yml", 10
            )
            Dataset.Validators.validate_iterate(sv, context)

            assert len(context.errors) == 0
            assert len(context.warnings) == 0

    def test_shuffle_valid_csv(self):
        """Test valid CSV dataset with shuffle"""
        with TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            csv_file = tmpdir_path / "data.csv"
            csv_file.write_text("col1,col2\nval1,val2\n")

            recipe_file = tmpdir_path / "recipe.yml"

            context = ValidationContext()
            context.current_template = type(
                "obj", (object,), {"filename": str(recipe_file)}
            )()

            sv = StructuredValue(
                "Dataset.shuffle", {"dataset": "data.csv"}, "recipe.yml", 10
            )
            Dataset.Validators.validate_shuffle(sv, context)

            assert len(context.errors) == 0
            assert len(context.warnings) == 0

    def test_valid_sql_url(self):
        """Test valid SQL database URL (no file check)"""
        context = ValidationContext()
        context.current_template = type("obj", (object,), {"filename": "test.yml"})()

        sv = StructuredValue(
            "Dataset.iterate",
            {"dataset": "sqlite:///data.db"},
            "test.yml",
            10,
        )
        Dataset.Validators.validate_iterate(sv, context)

        # Should pass validation (SQL URLs are not checked for existence)
        assert len(context.errors) == 0
        assert len(context.warnings) == 0

    def test_valid_with_table_param(self):
        """Test valid with table parameter"""
        context = ValidationContext()
        context.current_template = type("obj", (object,), {"filename": "test.yml"})()

        sv = StructuredValue(
            "Dataset.iterate",
            {"dataset": "postgresql://localhost/db", "table": "users"},
            "test.yml",
            10,
        )
        Dataset.Validators.validate_iterate(sv, context)

        assert len(context.errors) == 0
        assert len(context.warnings) == 0

    def test_valid_with_repeat_param(self):
        """Test valid with repeat parameter"""
        with TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            csv_file = tmpdir_path / "data.csv"
            csv_file.write_text("col1\nval1\n")

            recipe_file = tmpdir_path / "recipe.yml"

            context = ValidationContext()
            context.current_template = type(
                "obj", (object,), {"filename": str(recipe_file)}
            )()

            sv = StructuredValue(
                "Dataset.iterate",
                {"dataset": "data.csv", "repeat": False},
                "recipe.yml",
                10,
            )
            Dataset.Validators.validate_iterate(sv, context)

            assert len(context.errors) == 0
            assert len(context.warnings) == 0

    def test_missing_dataset_parameter(self):
        """Test error when dataset parameter is missing"""
        context = ValidationContext()
        sv = StructuredValue("Dataset.iterate", {}, "test.yml", 10)

        Dataset.Validators.validate_iterate(sv, context)

        assert len(context.errors) >= 1
        assert any(
            "missing required parameter" in err.message.lower()
            and "dataset" in err.message.lower()
            for err in context.errors
        )

    def test_csv_file_not_exists(self):
        """Test error when CSV file does not exist"""
        with TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            recipe_file = tmpdir_path / "recipe.yml"

            context = ValidationContext()
            context.current_template = type(
                "obj", (object,), {"filename": str(recipe_file)}
            )()

            sv = StructuredValue(
                "Dataset.iterate",
                {"dataset": "nonexistent.csv"},
                "recipe.yml",
                10,
            )
            Dataset.Validators.validate_iterate(sv, context)

            assert len(context.errors) >= 1
            assert any(
                "does not exist" in err.message.lower() for err in context.errors
            )

    def test_wrong_file_extension(self):
        """Test error when file doesn't have .csv extension"""
        with TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            recipe_file = tmpdir_path / "recipe.yml"

            context = ValidationContext()
            context.current_template = type(
                "obj", (object,), {"filename": str(recipe_file)}
            )()

            sv = StructuredValue(
                "Dataset.iterate",
                {"dataset": "data.txt"},
                "recipe.yml",
                10,
            )
            Dataset.Validators.validate_iterate(sv, context)

            assert len(context.errors) >= 1
            assert any(
                ".csv extension" in err.message.lower() for err in context.errors
            )

    def test_dataset_must_be_string(self):
        """Test error when dataset parameter is not a string"""
        context = ValidationContext()
        sv = StructuredValue("Dataset.iterate", {"dataset": 123}, "test.yml", 10)

        Dataset.Validators.validate_iterate(sv, context)

        assert len(context.errors) >= 1
        assert any(
            "must be a string" in err.message.lower()
            and "dataset" in err.message.lower()
            for err in context.errors
        )

    def test_table_must_be_string(self):
        """Test error when table parameter is not a string"""
        context = ValidationContext()
        context.current_template = type("obj", (object,), {"filename": "test.yml"})()

        sv = StructuredValue(
            "Dataset.iterate",
            {"dataset": "sqlite:///data.db", "table": 123},
            "test.yml",
            10,
        )
        Dataset.Validators.validate_iterate(sv, context)

        assert len(context.errors) >= 1
        assert any(
            "must be a string" in err.message.lower() and "table" in err.message.lower()
            for err in context.errors
        )

    def test_repeat_must_be_boolean(self):
        """Test error when repeat parameter is not a boolean"""
        with TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            csv_file = tmpdir_path / "data.csv"
            csv_file.write_text("col1\nval1\n")

            recipe_file = tmpdir_path / "recipe.yml"

            context = ValidationContext()
            context.current_template = type(
                "obj", (object,), {"filename": str(recipe_file)}
            )()

            sv = StructuredValue(
                "Dataset.iterate",
                {"dataset": "data.csv", "repeat": "false"},
                "recipe.yml",
                10,
            )
            Dataset.Validators.validate_iterate(sv, context)

            assert len(context.errors) >= 1
            assert any(
                "must be a boolean" in err.message.lower()
                and "repeat" in err.message.lower()
                for err in context.errors
            )

    def test_unknown_parameter(self):
        """Test warning for unknown parameters"""
        with TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            csv_file = tmpdir_path / "data.csv"
            csv_file.write_text("col1\nval1\n")

            recipe_file = tmpdir_path / "recipe.yml"

            context = ValidationContext()
            context.current_template = type(
                "obj", (object,), {"filename": str(recipe_file)}
            )()

            sv = StructuredValue(
                "Dataset.iterate",
                {"dataset": "data.csv", "mode": "linear"},
                "recipe.yml",
                10,
            )
            Dataset.Validators.validate_iterate(sv, context)

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
            subdir = tmpdir_path / "subdir.csv"  # Name it .csv to pass extension check
            subdir.mkdir()

            recipe_file = tmpdir_path / "recipe.yml"

            context = ValidationContext()
            context.current_template = type(
                "obj", (object,), {"filename": str(recipe_file)}
            )()

            sv = StructuredValue(
                "Dataset.iterate",
                {"dataset": "subdir.csv"},
                "recipe.yml",
                10,
            )
            Dataset.Validators.validate_iterate(sv, context)

            assert len(context.errors) >= 1
            assert any("is not a file" in err.message.lower() for err in context.errors)
