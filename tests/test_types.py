from unittest import mock
from io import StringIO

from snowfakery.data_generator import generate


class TestGenerateMapping:
    @mock.patch("snowfakery.output_streams.DebugOutputStream.write_row")
    def test_empty_string(self, write_row):
        yaml = """
            - object: Foo
              fields:
                bar: ""
        """
        generate(StringIO(yaml))
        print(write_row.mock_calls[0][1][1]["bar"] == "")
