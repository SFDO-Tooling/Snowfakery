from tempfile import TemporaryDirectory
from pathlib import Path
import yaml
from unittest import mock
from io import StringIO

import pytest

from snowfakery import generate_data
from snowfakery.data_generator_runtime import IdManager
from snowfakery.api import SnowfakeryApplication
from snowfakery import data_gen_exceptions as exc


class TestEmbedding:
    def test_simple_embedding(self):
        generate_data("tests/gender_conditional.yml")

    def test_embedding_dburl(self):
        with TemporaryDirectory() as t:
            dbpath = Path(t) / "foo.db"
            dburl = f"sqlite:///{dbpath}"
            generate_data("tests/gender_conditional.yml", dburl=dburl)
            assert dbpath.exists()

    def test_arguments(self):
        with TemporaryDirectory() as t, mock.patch("warnings.warn") as w:
            outfile = Path(t) / "foo.txt"
            continuation = Path(t) / "out.yml"
            generate_data(
                yaml_file="tests/BDI_generator.yml",
                user_options={"num_accounts": "15"},
                target_number=(20, "Account"),
                debug_internals=True,
                output_format="json",
                output_file=outfile,
                generate_continuation_file=continuation,
            )
            assert outfile.exists()
            assert continuation.exists()
            with continuation.open() as f:
                assert yaml.safe_load(f)
            assert "num_accounts" in str(w.mock_calls)

    def test_continuation_as_open_file(self):
        with TemporaryDirectory() as t:
            outfile = Path(t) / "foo.json"
            continuation = Path(t) / "cont.yml"
            mapping_file = Path(t) / "mapping.yml"
            with open(continuation, "w") as cont, open(mapping_file, "w") as mapf:
                generate_data(
                    yaml_file="examples/company.yml",
                    target_number=(20, "Employee"),
                    debug_internals=False,
                    output_file=outfile,
                    generate_continuation_file=cont,
                    generate_cci_mapping_file=mapf,
                )
            assert outfile.exists()
            assert continuation.exists()
            with continuation.open() as f:
                assert yaml.safe_load(f)
            assert mapping_file.exists()
            with mapping_file.open() as f:
                assert yaml.safe_load(f)

    def test_parent_application__echo(self):
        called = False

        class MyEmbedder(SnowfakeryApplication):
            def echo(self, *args, **kwargs):
                nonlocal called
                called = True

        meth = "snowfakery.output_streams.DebugOutputStream.close"
        with mock.patch(meth) as close:
            close.side_effect = AssertionError
            generate_data(
                yaml_file="examples/company.yml", parent_application=MyEmbedder()
            )
            assert called

    def test_parent_application__early_finish(self, generated_rows):
        class MyEmbedder(SnowfakeryApplication):
            count = 0

            def check_if_finished(self, idmanager):
                assert isinstance(idmanager, IdManager)
                self.__class__.count += 1
                assert self.__class__.count < 100, "Runaway recipe!"
                return idmanager["Employee"] >= 10

        meth = "snowfakery.output_streams.DebugOutputStream.close"
        with mock.patch(meth) as close:
            close.side_effect = AssertionError
            generate_data(
                yaml_file="examples/company.yml", parent_application=MyEmbedder()
            )
            # called 5 times, after generating 2 employees each
            assert MyEmbedder.count == 5

    def test_embedding__cannot_infer_output_format(self):
        with pytest.raises(exc.DataGenError, match="No format"):
            generate_data(
                yaml_file=StringIO("- object: Foo"),
                output_file=StringIO(),
            )

    def test_parent_application__streams_instead_of_files(self, generated_rows):
        yaml_file = StringIO("""- object: Foo""")
        generate_cci_mapping_file = StringIO()
        output_file = StringIO()
        output_files = [StringIO(), StringIO()]
        continuation_file = StringIO(
            """
        id_manager:
           last_used_ids:
             Foo: 6
        intertable_dependencies: []
        nicknames_and_tables:
           Foo: Foo
        persistent_nicknames: {}
        persistent_objects_by_table: {}
        today: 2021-04-07"""
        )
        generate_continuation_file = StringIO()
        decls = """[{"sf_object": Opportunity, "api": bulk}]"""
        load_declarations = [StringIO(decls), StringIO(decls)]

        generate_data(
            yaml_file=yaml_file,
            generate_cci_mapping_file=generate_cci_mapping_file,
            output_file=output_file,
            output_files=output_files,
            output_format="txt",
            continuation_file=continuation_file,
            generate_continuation_file=generate_continuation_file,
            load_declarations=load_declarations,
        )
        assert generated_rows.table_values("Foo", 0)["id"] == 7


class TestAPIValidation:
    """Test validation parameters in the generate_data API"""

    def test_api_strict_mode_with_valid_recipe(self):
        """Test strict_mode parameter with valid recipe"""
        with TemporaryDirectory() as t:
            recipe_path = Path(t) / "recipe.yml"
            recipe_path.write_text(
                """
- snowfakery_version: 3
- object: Account
  count: 2
  fields:
    Name: Test
    Score:
      random_number:
        min: 1
        max: 10
"""
            )
            result = generate_data(yaml_file=recipe_path, strict_mode=True)
            assert result is not None

    def test_api_strict_mode_catches_errors(self):
        """Test strict_mode catches validation errors via API"""
        with TemporaryDirectory() as t:
            recipe_path = Path(t) / "bad_recipe.yml"
            recipe_path.write_text(
                """
- snowfakery_version: 3
- object: Account
  fields:
    Score:
      random_number:
        min: 100
        max: 50
"""
            )
            from snowfakery.data_gen_exceptions import DataGenValidationError

            with pytest.raises(DataGenValidationError):
                generate_data(yaml_file=recipe_path, strict_mode=True)

    def test_api_validate_only_mode(self):
        """Test validate_only parameter returns ValidationResult"""
        with TemporaryDirectory() as t:
            recipe_path = Path(t) / "recipe.yml"
            recipe_path.write_text(
                """
- snowfakery_version: 3
- object: Account
  fields:
    Name: Test Account
"""
            )
            result = generate_data(yaml_file=recipe_path, validate_only=True)

            # Should return ValidationResult
            assert hasattr(result, "has_errors")
            assert hasattr(result, "has_warnings")
            assert not result.has_errors()

    def test_api_validate_only_with_errors(self):
        """Test validate_only detects errors via API"""
        with TemporaryDirectory() as t:
            recipe_path = Path(t) / "bad_recipe.yml"
            recipe_path.write_text(
                """
- snowfakery_version: 3
- object: Account
  fields:
    Value:
      unknown_function:
        param: value
"""
            )
            from snowfakery.data_gen_exceptions import DataGenValidationError

            with pytest.raises(DataGenValidationError):
                generate_data(yaml_file=recipe_path, validate_only=True)

    def test_api_backward_compatibility(self):
        """Test that default behavior hasn't changed (no validation)"""
        with TemporaryDirectory() as t:
            recipe_path = Path(t) / "recipe.yml"
            recipe_path.write_text(
                """
- snowfakery_version: 3
- object: Account
  count: 1
  fields:
    Name: Test
"""
            )
            # Default: no strict_mode, no validate_only
            result = generate_data(yaml_file=recipe_path)
            assert result is not None

    def test_api_with_stringio(self):
        """Test API validation with StringIO input"""
        recipe = StringIO(
            """
- snowfakery_version: 3
- object: Account
  fields:
    Score:
      random_number:
        min: 1
        max: 10
"""
        )
        result = generate_data(yaml_file=recipe, strict_mode=True)
        assert result is not None

    def test_api_validate_only_no_data_generation(self):
        """Test that validate_only doesn't generate actual data"""
        with TemporaryDirectory() as t:
            recipe_path = Path(t) / "recipe.yml"
            recipe_path.write_text(
                """
- snowfakery_version: 3
- object: Account
  count: 100
  fields:
    Name: Test
"""
            )
            result = generate_data(yaml_file=recipe_path, validate_only=True)

            # Should be ValidationResult, not ExecutionSummary with row counts
            assert hasattr(result, "has_errors")
            assert not hasattr(result, "row_counts")
