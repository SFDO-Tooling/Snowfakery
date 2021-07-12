from io import StringIO
from datetime import date

import pytest

from snowfakery.api import generate_data
from snowfakery.standard_plugins.UniqueId import as_bool
from snowfakery import data_gen_exceptions as exc


class TestUniqueIdBuiltin:
    def test_simple(self, generated_rows):
        yaml = """
        - object: Example
          count: 2
          fields:
            unique: ${{unique_id}}
        """
        generate_data(StringIO(yaml), plugin_options={"big_ids": "True"})
        assert str(generated_rows.row_values(0, "unique")).endswith("91")
        assert str(generated_rows.row_values(1, "unique")).endswith("92")

    def test_simple_iterations(self, generated_rows):
        yaml = """
        - plugin: snowfakery.standard_plugins.UniqueId
        - object: Example
          count: 2
          fields:
            unique: ${{UniqueId.unique_id}}
        """
        generate_data(StringIO(yaml), target_number=("Example", 4))
        assert generated_rows.row_values(0, "unique") == 1
        assert generated_rows.row_values(1, "unique") == 2
        assert generated_rows.row_values(2, "unique") == 3
        assert generated_rows.row_values(3, "unique") == 4


class TestAlphaCodeBuiltiin:
    def test_alpha_code(self, generated_rows):
        yaml = """
        - object: Example
          count: 2
          fields:
            unique: ${{unique_alpha_code}}
        """
        generate_data(StringIO(yaml))
        assert len(generated_rows.row_values(0, "unique")) >= 8
        assert len(generated_rows.row_values(1, "unique")) >= 8

    def test_alpha_code_small_ids(self, generated_rows):
        yaml = """
        - object: Example
          count: 2
          fields:
            unique: ${{unique_alpha_code}}
        """
        generate_data(StringIO(yaml), plugin_options={"big_ids": "False"})
        assert len(generated_rows.row_values(0, "unique")) >= 8
        assert len(generated_rows.row_values(1, "unique")) >= 8


class TestNumericIdGenerator:
    def test_custom_multipart(self, generated_rows):
        yaml = """
        - plugin: snowfakery.standard_plugins.UniqueId
        - var: MyGenerator
          value:
            UniqueId.NumericIdGenerator: 5, index
        - object: Example
          count: 2
          fields:
            unique: ${{MyGenerator.unique_id}}
        """
        generate_data(StringIO(yaml), plugin_options={"big_ids": "False"})
        assert str(generated_rows.row_values(0, "unique")) == "591"
        assert str(generated_rows.row_values(1, "unique")) == "592"

    def test_with_pid(self, generated_rows):
        yaml = """
        - plugin: snowfakery.standard_plugins.UniqueId
        - var: MyGenerator
          value:
            UniqueId.NumericIdGenerator: pid, 5, index
        - object: Example
          count: 2
          fields:
            unique: ${{MyGenerator.unique_id}}
        """
        generate_data(StringIO(yaml))
        assert str(generated_rows.row_values(0, "unique")).endswith("591")

    def test_with_pid_option(self, generated_rows):
        yaml = """
        - plugin: snowfakery.standard_plugins.UniqueId
        - var: MyGenerator
          value:
            UniqueId.NumericIdGenerator: pid, 9, index
        - object: Example
          count: 2
          fields:
            unique: ${{MyGenerator.unique_id}}
        """
        generate_data(StringIO(yaml), plugin_options={"pid": "3"})
        assert str(generated_rows.row_values(0, "unique")) == "391191"

    def test_bad_template(self):
        yaml = """
        - plugin: snowfakery.standard_plugins.UniqueId
        - var: MyGenerator
          value:
            UniqueId.NumericIdGenerator: pid, foo, 9, index
        - object: Example
          count: 2
          fields:
            unique: ${{MyGenerator.unique_id}}
        """
        with pytest.raises(exc.DataGenError) as e:
            generate_data(StringIO(yaml), plugin_options={"pid": "3"})
        assert "foo" in str(e.value)

    def test_bad_template__2(self):
        yaml = """
        - plugin: snowfakery.standard_plugins.UniqueId
        - var: MyGenerator
          value:
            UniqueId.NumericIdGenerator: pid, 9.7, index
        - object: Example
          count: 2
          fields:
            unique: ${{MyGenerator.unique_id}}
        """
        with pytest.raises(exc.DataGenError) as e:
            generate_data(StringIO(yaml), plugin_options={"pid": "3"})
        assert "9.7" in str(e.value)


class TestAlphaCodeGenerator:
    def test_alpha(self, generated_rows):
        yaml = """
        - plugin: snowfakery.standard_plugins.UniqueId
        - var: MyGenerator
          value:
            UniqueId.AlphaCodeGenerator: pid,index
        - object: Example
          count: 2
          fields:
            unique: ${{MyGenerator.unique_id}}
        """
        generate_data(
            StringIO(yaml),
            plugin_options={"big_ids": "True", "pid": "3333333333333333"},
        )
        assert len(generated_rows.row_values(0, "unique")) > 8
        assert len(generated_rows.row_values(1, "unique")) > 8

    def test_custom_alphabets(self, generated_rows):
        with open("examples/unique_id/alphabet.recipe.yml") as f:
            generate_data(f)
        assert len(generated_rows.row_values(0, "big_alpha_example")) > 6
        assert set(generated_rows.row_values(0, "dna_example")).issubset("ACGT")
        assert set(str(generated_rows.row_values(0, "num_example"))).issubset(
            "0123456789"
        )

    def test_alpha_small(self, generated_rows):
        with open("examples/unique_id/min_length.recipe.yml") as f:
            generate_data(
                f,
                plugin_options={"big_ids": "False"},
            )
        assert len(generated_rows.row_values(0, "unique")) == 6
        assert len(generated_rows.row_values(1, "unique")) == 6

    def test_alpha_small_sequential(self, generated_rows):
        yaml = """
        - plugin: snowfakery.standard_plugins.UniqueId
        - var: MyGenerator
          value:
            UniqueId.AlphaCodeGenerator:
              template: index
              min_chars: 4
              randomize_codes: False
        - object: Example
          count: 10
          fields:
            unique: ${{MyGenerator.unique_id}}
        """
        generate_data(
            StringIO(yaml),
            plugin_options={"big_ids": "True"},
        )
        assert len(generated_rows.row_values(0, "unique")) == 4
        assert len(generated_rows.row_values(1, "unique")) == 4
        assert len(generated_rows.row_values(9, "unique")) == 4

    def test_alpha_small_sequential_with_template(self, generated_rows):
        yaml = """
        - plugin: snowfakery.standard_plugins.UniqueId
        - var: MyGenerator
          value:
            UniqueId.AlphaCodeGenerator:
              template: 3,index
              min_chars: 4
              randomize_codes: False
        - object: Example
          count: 10
          fields:
            unique: ${{MyGenerator.unique_id}}
        """
        generate_data(
            StringIO(yaml),
            plugin_options={"big_ids": "True"},
        )
        assert len(generated_rows.row_values(0, "unique")) == 4
        assert len(generated_rows.row_values(1, "unique")) == 4
        assert len(generated_rows.row_values(9, "unique")) == 4

    def test_alpha_custom_alphabet_min_chars(self, generated_rows):
        yaml = """
        - plugin: snowfakery.standard_plugins.UniqueId
        - var: MyGenerator
          value:
            UniqueId.AlphaCodeGenerator:
              template: 3,index
              min_chars: 1000
              randomize_codes: False
              alphabet: ABC123!
        - object: Example
          count: 1
          fields:
            unique: ${{MyGenerator.unique_id}}
        """
        generate_data(
            StringIO(yaml),
            plugin_options={"big_ids": "True"},
        )
        assert len(generated_rows.row_values(0, "unique")) >= 1000
        assert set(generated_rows.row_values(0, "unique")).issubset(set("ABC123!"))

    def test_alpha_custom_alphabet_random(self, generated_rows):
        yaml = """
        - plugin: snowfakery.standard_plugins.UniqueId
        - var: MyGenerator
          value:
            UniqueId.AlphaCodeGenerator:
              template: 9999,index
              min_chars: 20
              randomize_codes: True
              alphabet: ABC123!
        - object: Example
          count: 1
          fields:
            unique: ${{MyGenerator.unique_id}}
        """
        generate_data(
            StringIO(yaml),
            plugin_options={"big_ids": "True"},
        )
        assert len(generated_rows.row_values(0, "unique")) >= 20
        assert set(generated_rows.row_values(0, "unique")).issubset(set("ABC123!"))

    def test_alpha_large_sequential_with_template(self, generated_rows):
        yaml = """
        - plugin: snowfakery.standard_plugins.UniqueId
        - var: MyGenerator
          value:
            UniqueId.AlphaCodeGenerator:
              template: 3,index
              min_chars: 20
              randomize_codes: False
        - object: Example
          count: 10
          fields:
            unique: ${{MyGenerator.unique_id}}
        """
        generate_data(StringIO(yaml), plugin_options={"big_ids": "True"})
        assert len(generated_rows.row_values(0, "unique")) >= 20


class TestCounter:
    def test_counter(self, generated_rows):
        with open("examples/test_counter.recipe.yml") as f:
            generate_data(f)
        assert generated_rows.row_values(0, "count") == 1
        assert generated_rows.row_values(9, "count") == 10

    def test_counter_start(self, generated_rows):
        with open("examples/test_counter_start.recipe.yml") as f:
            generate_data(f)
        assert generated_rows.row_values(0, "count") == 11
        assert generated_rows.row_values(9, "count") == 38

    def test_counter_iterations(self, generated_rows):
        with open("examples/test_counter.recipe.yml") as f:
            generate_data(f, target_number=("Example", 20))
        assert generated_rows.row_values(0, "count") == 1
        assert generated_rows.row_values(9, "count") == 10
        assert generated_rows.row_values(10, "count") == 11


class TestAsBool:
    def test_bool_conversions(self):
        assert as_bool("False") is False
        assert as_bool("0") is False
        assert as_bool("no") is False
        assert as_bool(0) is False
        assert as_bool(False) is False
        assert as_bool("True") is True
        assert as_bool("1") is True
        assert as_bool("YES") is True
        assert as_bool(1) is True
        assert as_bool(True) is True
        with pytest.raises(TypeError):
            as_bool("BLAH")
        with pytest.raises(TypeError):
            as_bool(3.145)


class TestDateCounter:
    def test_date_counter(self, generated_rows):
        with open("examples/unique_id/date_counter.recipe.yml") as f:
            generate_data(f, target_number=("TV_Episode", 20))
        assert generated_rows.row_values(0, "date") == "2021-12-12"
        assert generated_rows.row_values(24, "date") == "2023-01-02"

    def test_date_counter_relative(self, generated_rows):
        yaml = """
          - plugin: snowfakery.standard_plugins.UniqueId
          - var: SeriesStarts
            just_once: True
            value:
              UniqueId.DateCounter:
                start_date: today
                step: +3M
          - object: TV_Series
            count: 2
            fields:
              date: ${{SeriesStarts.next}}
        """
        generate_data(StringIO(yaml))
        start_date = date.fromisoformat(generated_rows.row_values(0, "date"))
        end_date = date.fromisoformat(generated_rows.row_values(1, "date"))
        delta = end_date - start_date
        assert 89 <= delta.days <= 91
