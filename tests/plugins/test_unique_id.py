from io import StringIO

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
        assert generated_rows.row_values(0, "unique")
        assert generated_rows.row_values(1, "unique")

    def test_simple_iterations(self, generated_rows):
        yaml = """
        - plugin: snowfakery.standard_plugins.UniqueId
        - object: Example
          count: 2
          fields:
            unique: ${{UniqueId.unique_id}}
        """
        generate_data(
            StringIO(yaml),
            target_number=("Example", 4),
            plugin_options={"big_ids": "False"},
        )
        assert generated_rows.row_values(0, "unique")
        assert generated_rows.row_values(1, "unique")
        assert generated_rows.row_values(2, "unique")
        assert generated_rows.row_values(3, "unique")

    def test_continuations(self, generate_data_with_continuation, generated_rows):
        yaml = """
        - plugin: snowfakery.standard_plugins.UniqueId
        - object: Example
          just_once: True
          fields:
            __uniquifier:
              UniqueId.NumericIdGenerator:
            unique: ${{__uniquifier.unique_id}}
        - object: Example
          count: 2
          fields:
            __uniquifier:
              UniqueId.NumericIdGenerator:
            unique: ${{__uniquifier.unique_id}}
        """
        generate_data_with_continuation(
            yaml=yaml,
            target_number=("Example", 1),
            times=3,
            plugin_options={"big_ids": "False"},
        )
        a = generated_rows.row_values(0, "unique")
        b = generated_rows.row_values(1, "unique")
        c = generated_rows.row_values(2, "unique")
        d = generated_rows.row_values(3, "unique")
        assert all([a, b, c, d])
        assert len(set([a, b, c, d])) == 4


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
            UniqueId.NumericIdGenerator:
              template: 5, index
        - object: Example
          count: 2
          fields:
            unique: ${{MyGenerator.unique_id}}
        """
        generate_data(StringIO(yaml), plugin_options={"big_ids": "False"})
        assert str(generated_rows.row_values(0, "unique"))
        assert str(generated_rows.row_values(1, "unique"))

    def test_with_pid(self, generated_rows):
        yaml = """
        - plugin: snowfakery.standard_plugins.UniqueId
        - var: MyGenerator
          value:
            UniqueId.NumericIdGenerator:
              template: pid, 5, index
        - object: Example
          count: 2
          fields:
            unique: ${{MyGenerator.unique_id}}
        """
        generate_data(StringIO(yaml))
        assert generated_rows.row_values(0, "unique")

    def test_with_pid_option(self, generated_rows):
        yaml = """
        - plugin: snowfakery.standard_plugins.UniqueId
        - var: MyGenerator
          value:
            UniqueId.NumericIdGenerator:
              template: pid, 9, index
        - object: Example
          count: 2
          fields:
            unique: ${{MyGenerator.unique_id}}
        """
        generate_data(StringIO(yaml), plugin_options={"pid": "3"})
        assert generated_rows.row_values(0, "unique")

    def test_bad_template(self):
        yaml = """
        - plugin: snowfakery.standard_plugins.UniqueId
        - var: MyGenerator
          value:
            UniqueId.NumericIdGenerator:
              template: pid, foo, 9, index
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
            UniqueId.NumericIdGenerator:
              template: pid, 9.7, index
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
        assert len(generated_rows.row_values(0, "unique")) == 1000
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
