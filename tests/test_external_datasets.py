from pathlib import Path
from io import StringIO
from unittest import mock

import pytest

from snowfakery.data_generator import generate
from snowfakery import data_gen_exceptions as exc
from snowfakery.standard_plugins.datasets import SQLDatasetRandomPermutationIterator


class TestExternalDatasets:
    def test_csv_dataset_linear(self, generated_rows):
        abs_path = str(Path(__file__).parent)
        yaml = (
            """
        - plugin: snowfakery.standard_plugins.datasets.Dataset
        - object: XXX
          count: 10
          fields:
            __address_from_csv:
              Dataset.iterate:
                dataset: %s/../examples/datasets/addresses.csv
            City: ${{__address_from_csv.City}}
        """
            % abs_path
        )
        generate(StringIO(yaml), {})
        assert generated_rows.row_values(0, "City") == "Burnaby"
        assert generated_rows.row_values(1, "City") == "White Rock"
        # wraps around:
        assert generated_rows.row_values(7, "City") == "White Rock"
        assert generated_rows.row_values(8, "City") == "Richmond"

    def test_SQL_dataset_linear(self, generated_rows):
        abs_path = str(Path(__file__).parent)
        yaml = (
            """
        - plugin: snowfakery.standard_plugins.datasets.Dataset
        - object: XXX
          count: 10
          fields:
            __name_from_db:
              Dataset.iterate:
                dataset: sqlite:///%s/databases/test_db.db
            FirstName: ${{__name_from_db.first_name}}
            LastName: ${{__name_from_db.last_name}}
        """
            % abs_path
        )
        generate(StringIO(yaml), {})
        assert generated_rows.row_values(0, "FirstName") == "Test"
        assert generated_rows.row_values(0, "LastName") == "User"
        assert generated_rows.row_values(1, "FirstName") == "Zest"
        # wraps around:
        assert generated_rows.row_values(7, "FirstName") == "Test"
        assert generated_rows.row_values(7, "LastName") == "User"
        assert generated_rows.row_values(8, "FirstName") == "Zest"

    def test_csv_dataset_permutation(self, generated_rows):
        abs_path = str(Path(__file__).parent)
        yaml = (
            """
        - plugin: snowfakery.standard_plugins.datasets.Dataset
        - object: XXX
          count: 14
          fields:
            __address_from_csv:
              Dataset.shuffle:
                dataset: %s/../examples/datasets/addresses.csv
            City: ${{__address_from_csv.City}}
        """
            % abs_path
        )
        generate(StringIO(yaml), {})
        first_3 = [generated_rows.row_values(i, "City") for i in range(0, 3)]
        assert len(first_3) == len(set(first_3))  # 3 unique items, in some order
        next_3 = [generated_rows.row_values(i, "City") for i in range(3, 14)]
        assert set(first_3) == set(next_3)

    def test_SQL_dataset_permutation(self, generated_rows):
        abs_path = str(Path(__file__).parent)
        yaml = (
            """
        - plugin: snowfakery.standard_plugins.datasets.Dataset
        - object: XXX
          count: 14
          fields:
            __name_from_db:
              Dataset.shuffle:
                dataset: sqlite:///%s/databases/test_db.db
                table: contacts
            FirstName: ${{__name_from_db.first_name}}
            LastName: ${{__name_from_db.last_name}}
        """
            % abs_path
        )
        generate(StringIO(yaml), {})
        first_7 = [generated_rows.row_values(i, "FirstName") for i in range(0, 7)]
        assert len(first_7) == len(set(first_7))  # 7 unique items, in some order
        next_7 = [generated_rows.row_values(i, "FirstName") for i in range(7, 14)]
        assert set(first_7) == set(next_7)

    def test_SQL_dataset_permutation_really_shuffles(self, generated_rows):
        abs_path = str(Path(__file__).parent)
        yaml = (
            """
        - plugin: snowfakery.standard_plugins.datasets.Dataset
        - object: XXX
          count: 14
          fields:
            __name_from_db:
              Dataset.shuffle:
                dataset: sqlite:///%s/databases/test_db.db
                table: contacts
            FirstName: ${{__name_from_db.first_name}}
            LastName: ${{__name_from_db.last_name}}
        """
            % abs_path
        )

        orig_query = SQLDatasetRandomPermutationIterator.query

        called = None

        def new_query(self):
            nonlocal called
            called = True
            return orig_query(self)

        with mock.patch(
            "snowfakery.standard_plugins.datasets.SQLDatasetRandomPermutationIterator.query",
            new_query,
        ):
            generate(StringIO(yaml), {})
        assert called

    def test_csv_missing(self):
        abs_path = str(Path(__file__).parent)
        yaml = (
            """
        - plugin: snowfakery.standard_plugins.datasets.Dataset
        - object: XXX
          fields:
            __address_from_csv:
              Dataset.iterate:
                dataset: %s/test_csv_missing.csv
        """
            % abs_path
        )
        with pytest.raises(exc.DataGenError) as e:
            generate(StringIO(yaml), {})
        assert "File not found" in str(e.value)

    def test_csv_wrong_name(self):
        abs_path = str(Path(__file__).parent)
        yaml = (
            """
        - plugin: snowfakery.standard_plugins.datasets.Dataset
        - object: XXX
          fields:
            __address_from_csv:
              Dataset.iterate:
                dataset: %s/test_external_datasets.py
        """
            % abs_path
        )
        with pytest.raises(exc.DataGenError) as e:
            generate(StringIO(yaml), {})
        assert "Filename extension must be .csv" in str(e.value)

    def test_csv_bad_column_name(self):
        abs_path = str(Path(__file__).parent)
        yaml = (
            """
        - plugin: snowfakery.standard_plugins.datasets.Dataset
        - object: XXX
          fields:
            __address_from_csv:
              Dataset.iterate:
                dataset: %s/badcsv.csv
            foo: ${{__address_from_csv.name}}
        """
            % abs_path
        )
        with pytest.raises(exc.DataGenError) as e:
            generate(StringIO(yaml), {})
        assert "'xname ', 'fake'" in str(e.value)

    def test_csv_row_has_too_many_columns(self):
        abs_path = str(Path(__file__).parent)
        yaml = (
            """
        - plugin: snowfakery.standard_plugins.datasets.Dataset
        - object: XXX
          fields:
            __address_from_csv:
              Dataset.iterate:
                dataset: %s/badcsv_too_many_columns.csv
            foo: ${{__address_from_csv.name}}
        """
            % abs_path
        )
        with pytest.raises(exc.DataGenError) as e:
            generate(StringIO(yaml), {})
        assert "more columns" in str(e.value)

    def test_csv_utf_8_bom(self, generated_rows):
        abs_path = Path(__file__).parent
        yaml = (
            """
        - plugin: snowfakery.standard_plugins.datasets.Dataset
        - object: XXX
          fields:
            __address_from_csv:
              Dataset.iterate:
                dataset: %s/utf_8_bom_csv.csv
            foo: ${{__address_from_csv.name}}
        """
            % abs_path
        )
        with (abs_path / "utf_8_bom_csv.csv").open("rb") as f:
            assert f.read(10).startswith(b"\xef\xbb\xbf")
        generate(StringIO(yaml), {})
        assert generated_rows.table_values("XXX", 1, "foo") == "Afghanistan"

    def test_SQL_dataset_bad_tablename(self, generated_rows):
        abs_path = str(Path(__file__).parent)
        yaml = (
            """
        - plugin: snowfakery.standard_plugins.datasets.Dataset
        - object: XXX
          count: 14
          fields:
            __name_from_db:
              Dataset.iterate:
                dataset: sqlite:///%s/databases/test_db.db
                table: xyzzy
            FirstName: ${{__name_from_db.first_name}}
            LastName: ${{__name_from_db.last_name}}
        """
            % abs_path
        )
        with pytest.raises(exc.DataGenError) as e:
            generate(StringIO(yaml), {})

        assert "Cannot find table: xyzzy" in str(e.value)

    def test_SQL_dataset_missing_table(self, generated_rows):
        yaml = """
        - plugin: snowfakery.standard_plugins.datasets.Dataset
        - object: XXX
          fields:
            __name_from_db:
              Dataset.iterate:
                dataset: sqlite:///tests/databases/missing_db.db
        """
        with pytest.raises(exc.DataGenError) as e:
            generate(StringIO(yaml), {})

        assert "no tables" in str(e.value)

    def test_SQL_dataset_missing_file(self, generated_rows):
        yaml = """
        - plugin: snowfakery.standard_plugins.datasets.Dataset
        - object: XXX
          fields:
            __name_from_db:
              Dataset.iterate:
                dataset: sqlite:////xxxxyzzz/missing_db.db
        """
        with pytest.raises(exc.DataGenError) as e:
            generate(StringIO(yaml), {})

        assert "unable to open database file" in str(e.value)

    def test_SQL_dataset_multitable_file(self):
        abs_path = str(Path(__file__).parent)
        yaml = (
            """
        - plugin: snowfakery.standard_plugins.datasets.Dataset
        - object: XXX
          count: 14
          fields:
            __name_from_db:
              Dataset.iterate:
                dataset: sqlite:///%s/databases/multitable.db
            FirstName: ${{__name_from_db.first_name}}
            LastName: ${{__name_from_db.last_name}}
        """
            % abs_path
        )
        with pytest.raises(exc.DataGenError) as e:
            generate(StringIO(yaml), {})

        assert "multiple tables in it" in str(e.value)

    def test_datasets_example(self, capsys, caplog):
        """Datasets can output warnings if they don't close properly.
        This test checks that they DO close properly and DO NOT output warnings."""
        with open(
            Path(__file__).parent.parent / "examples/datasets/datasets.recipe.yml"
        ) as f:
            generate(f, {})
            assert capsys.readouterr().err == ""
            assert caplog.text == ""

    def test_nested_for_loops(self, generated_rows):
        call = mock.call
        with open(
            Path(__file__).parent.parent
            / "examples/datasets/nested_for_loops.recipe.yml"
        ) as f:
            generate(f, {})
        assert generated_rows.mock_calls == [
            call("Foo", {"id": 1, "StreetAddress": "420 Kings Ave", "City": "Burnaby"}),
            call(
                "Person", {"id": 1, "StreetAddress": "420 Kings Ave", "City": "Burnaby"}
            ),
            call(
                "Person",
                {"id": 2, "StreetAddress": "421 Granville Street", "City": "Burnaby"},
            ),
            call(
                "Person",
                {"id": 3, "StreetAddress": "422 Kingsway Road", "City": "Burnaby"},
            ),
            call(
                "Foo",
                {
                    "id": 2,
                    "StreetAddress": "421 Granville Street",
                    "City": "White Rock",
                },
            ),
            call(
                "Person",
                {"id": 4, "StreetAddress": "420 Kings Ave", "City": "White Rock"},
            ),
            call(
                "Person",
                {
                    "id": 5,
                    "StreetAddress": "421 Granville Street",
                    "City": "White Rock",
                },
            ),
            call(
                "Person",
                {"id": 6, "StreetAddress": "422 Kingsway Road", "City": "White Rock"},
            ),
            call(
                "Foo",
                {"id": 3, "StreetAddress": "422 Kingsway Road", "City": "Richmond"},
            ),
            call(
                "Person",
                {"id": 7, "StreetAddress": "420 Kings Ave", "City": "Richmond"},
            ),
            call(
                "Person",
                {"id": 8, "StreetAddress": "421 Granville Street", "City": "Richmond"},
            ),
            call(
                "Person",
                {"id": 9, "StreetAddress": "422 Kingsway Road", "City": "Richmond"},
            ),
        ]

    def test_for_loop_over_empty_dataset(self, generated_rows):
        with open(
            Path(__file__).parent.parent / "examples/datasets/empty_dataset.recipe.yml"
        ) as f:
            generate(f, {})
        assert len(generated_rows.mock_calls) == 1

    def test_for_loop_over_bad_type__int(self, generated_rows):
        yaml = """
        - object: Person
          for_each:
            var: blah
            value: 11"""

        with pytest.raises(exc.DataGenError) as e:
            generate(StringIO(yaml), {})
        assert "value" in str(e.value)

    def test_for_loop_over_bad_type__str(self, generated_rows):
        yaml = """
        - object: Person
          for_each:
            var: blah
            value: "eleven" """

        with pytest.raises(exc.DataGenError) as e:
            generate(StringIO(yaml), {})
        assert "blah" in str(e.value)

    def test_for_loop_and_count_error(self, generated_rows):
        yaml = """
        -   object: Person
            count: 10
            for_each:
                var: blah
                value: "eleven" """

        with pytest.raises(exc.DataGenSyntaxError) as e:
            generate(StringIO(yaml), {})
        assert "Person" in str(e.value)

    def test_for_loop_no_vardef_error__scalar(self, generated_rows):
        yaml = """
        -   object: Person
            count: 10
            for_each: 5
        """

        with pytest.raises(exc.DataGenSyntaxError) as e:
            generate(StringIO(yaml), {})
        assert "for_each" in str(e.value)

    def test_for_loop_no_vardef_error__dict(self, generated_rows):
        yaml = """
        -   object: Person
            count: 10
            for_each:
                foo: bar
        """

        with pytest.raises(exc.DataGenSyntaxError) as e:
            generate(StringIO(yaml), {})
        assert "foo" in str(e.value)
