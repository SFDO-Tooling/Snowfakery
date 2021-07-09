from io import StringIO

from snowfakery.data_generator import generate


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
        generate(StringIO(yaml))
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
