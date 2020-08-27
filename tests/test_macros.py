import unittest
from unittest import mock
from io import StringIO

from snowfakery.data_generator import generate

write_row_path = "snowfakery.output_streams.DebugOutputStream.write_row"


class TestMacros(unittest.TestCase):
    @mock.patch("snowfakery.output_streams.DebugOutputStream.write_row")
    def test_field_includes(self, write_row):
        yaml = """
        - macro: standard_foo
          fields:
            bar: 5

        - object: foo
          include: standard_foo
          fields:
            baz: 6
        """
        generate(StringIO(yaml))
        assert write_row.mock_calls == [mock.call("foo", {"id": 1, "bar": 5, "baz": 6})]

    @mock.patch("snowfakery.output_streams.DebugOutputStream.write_row")
    def test_friend_includes(self, write_row):
        yaml = """
        - macro: standard_foo
          friends:
            - object: bar

        - object: foo
          include: standard_foo
        """
        generate(StringIO(yaml))
        assert write_row.mock_calls == [
            mock.call("foo", {"id": 1}),
            mock.call("bar", {"id": 1}),
        ]

    @mock.patch("snowfakery.output_streams.DebugOutputStream.write_row")
    def test_field_and_friend_includes(self, write_row):
        yaml = """
        - macro: standard_foo
          fields:
              bar: 5

          friends:
            - object: baz
              fields:
                zar: 6

        - object: foo
          include: standard_foo
        """
        generate(StringIO(yaml))
        assert write_row.mock_calls == [
            mock.call("foo", {"id": 1, "bar": 5}),
            mock.call("baz", {"id": 1, "zar": 6}),
        ]

    @mock.patch("snowfakery.output_streams.DebugOutputStream.write_row")
    def test_friend_includes_and_references(self, write_row):
        yaml = """
        - macro: standard_foo
          friends:
            - object: bar
              fields:
                 myfoo:
                    reference: foo

        - object: foo
          include: standard_foo
        """
        generate(StringIO(yaml))
        assert write_row.mock_calls[0] == mock.call("foo", {"id": 1})
        assert write_row.mock_calls[1][1][0] == "bar"
        assert write_row.mock_calls[1][1][1]["myfoo"].id == 1

    @mock.patch("snowfakery.output_streams.DebugOutputStream.write_row")
    def test_macros_include_macros(self, write_row):
        yaml = """
        - macro: foo
          fields:
            foobar: FOOBAR

        - macro: bar
          include: foo
          fields:
            barbar: BARBAR

        - object: Bar
          include: bar
        """
        generate(StringIO(yaml))
        assert write_row.mock_calls[0] == mock.call(
            "Bar", {"id": 1, "barbar": "BARBAR", "foobar": "FOOBAR"}
        )
