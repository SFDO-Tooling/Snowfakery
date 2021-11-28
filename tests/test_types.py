from unittest import mock
from io import StringIO

from snowfakery.data_generator import generate


class TestTypes:
    @mock.patch("snowfakery.output_streams.DebugOutputStream.write_row")
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
