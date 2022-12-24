import pytest
from io import StringIO

from snowfakery.data_generator import generate


class TestTypes:
    def test_empty_string(self, write_row):
        yaml = """
            - object: Foo
              fields:
                bar: ""
        """
        generate(StringIO(yaml))
        assert write_row.mock_calls[0][1][1]["bar"] == ""

    def test_zero_prefixed_string(self, generated_rows):
        yaml = """
            - object: Foo
              fields:
                bar: "012345"
                bar2: ${{"012345"}}
        """
        generate(StringIO(yaml))
        assert generated_rows.row_values(0, "bar") == "012345"
        assert generated_rows.row_values(0, "bar2") == "012345"

    def test_float(self, generated_rows):
        yaml = """
            - object: Foo
              fields:
                foo: 0.1
                foo2: ${{0.1}}
        """
        generate(StringIO(yaml))
        assert generated_rows.row_values(0, "foo") == 0.1
        assert generated_rows.row_values(0, "foo2") == 0.1

    @pytest.mark.parametrize("snowfakery_version", (2, 3))
    def test_decimal(self, generated_rows, snowfakery_version):
        with open("tests/decimal.yml") as f:
            generate(f, plugin_options={"snowfakery_version": snowfakery_version})
        assert isinstance(
            generated_rows.table_values("Foo", 0)["lat"], float
        )  # Jinja quirk
        assert isinstance(generated_rows.table_values("Bar", 0)["lat2"], str)
        assert isinstance(generated_rows.table_values("Baz", 0)["lat3"], str)
