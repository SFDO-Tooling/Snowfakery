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

    def test_csv_missing(self, generated_rows):
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

    def test_csv_wrong_name(self, generated_rows):
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

    def test_SQL_dataset_multitable_file(self, generated_rows):
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
