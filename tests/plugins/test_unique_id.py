from io import StringIO

import pytest

from snowfakery.data_generator import generate
from snowfakery.standard_plugins.UniqueId import as_bool
from snowfakery import data_gen_exceptions as exc


class TestUniqueId:
    def test_simple(self, generated_rows):
        yaml = """
        - object: Example
          count: 2
          fields:
            unique: ${{unique_id}}
        """
        generate(StringIO(yaml), plugin_options={"big_ids": "True"})
        assert str(generated_rows.row_values(0, "unique")).endswith("91")
        assert str(generated_rows.row_values(1, "unique")).endswith("92")

    def test_simple_plugin_syntaxs(self, generated_rows):
        yaml = """
        - plugin: snowfakery.standard_plugins.UniqueId
        - object: Example
          count: 2
          fields:
            unique: ${{UniqueId.unique_id}}
        """
        generate(StringIO(yaml), plugin_options={"big_ids": "True"})
        assert str(generated_rows.row_values(0, "unique")).endswith("91")
        assert str(generated_rows.row_values(1, "unique")).endswith("92")

    def test_custom_simple(self, generated_rows):
        yaml = """
        - plugin: snowfakery.standard_plugins.UniqueId
        - var: MyGenerator
          value:
            UniqueId.Generator: index
        - object: Example
          count: 10
          fields:
            unique: ${{MyGenerator.unique_id}}
        """
        generate(StringIO(yaml))
        assert str(generated_rows.row_values(0, "unique")) == "1"
        assert str(generated_rows.row_values(1, "unique")) == "2"
        assert str(generated_rows.row_values(9, "unique")) == "12"

    def test_custom_multipart(self, generated_rows):
        yaml = """
        - plugin: snowfakery.standard_plugins.UniqueId
        - var: MyGenerator
          value:
            UniqueId.Generator: 5, index
        - object: Example
          count: 2
          fields:
            unique: ${{MyGenerator.unique_id}}
        """
        generate(StringIO(yaml), plugin_options={"big_ids": "False"})
        assert str(generated_rows.row_values(0, "unique")) == "591"
        assert str(generated_rows.row_values(1, "unique")) == "592"

    def test_with_pid(self, generated_rows):
        yaml = """
        - plugin: snowfakery.standard_plugins.UniqueId
        - var: MyGenerator
          value:
            UniqueId.Generator: pid, 5, index
        - object: Example
          count: 2
          fields:
            unique: ${{MyGenerator.unique_id}}
        """
        generate(StringIO(yaml))
        assert str(generated_rows.row_values(0, "unique")).endswith("591")

    def test_with_pid_option(self, generated_rows):
        yaml = """
        - plugin: snowfakery.standard_plugins.UniqueId
        - var: MyGenerator
          value:
            UniqueId.Generator: pid, 9, index
        - object: Example
          count: 2
          fields:
            unique: ${{MyGenerator.unique_id}}
        """
        generate(StringIO(yaml), plugin_options={"pid": "3"})
        assert str(generated_rows.row_values(0, "unique")) == "391191"

    def test_bad_template(self):
        yaml = """
        - plugin: snowfakery.standard_plugins.UniqueId
        - var: MyGenerator
          value:
            UniqueId.Generator: pid, foo, 9, index
        - object: Example
          count: 2
          fields:
            unique: ${{MyGenerator.unique_id}}
        """
        with pytest.raises(exc.DataGenError) as e:
            generate(StringIO(yaml), plugin_options={"pid": "3"})
        assert "foo" in str(e.value)

    def test_bad_template__2(self):
        yaml = """
        - plugin: snowfakery.standard_plugins.UniqueId
        - var: MyGenerator
          value:
            UniqueId.Generator: pid, 9.7, index
        - object: Example
          count: 2
          fields:
            unique: ${{MyGenerator.unique_id}}
        """
        with pytest.raises(exc.DataGenError) as e:
            generate(StringIO(yaml), plugin_options={"pid": "3"})
        assert "9.7" in str(e.value)

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
