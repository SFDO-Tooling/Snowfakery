import unittest
from unittest import mock
from io import StringIO

from snowfakery.data_generator import generate


class TestRestart(unittest.TestCase):
    @mock.patch("snowfakery.output_streams.DebugOutputStream.write_row")
    def test_nicknames_persist(self, write_row):
        yaml = """
            - object: foo
              nickname: Foo
            - object: bar
              fields:
                foo_reference:
                    reference: Foo
            """
        continuation_file = StringIO()
        generate(StringIO(yaml), generate_continuation_file=continuation_file)
        generate(
            StringIO(yaml), continuation_file=StringIO(continuation_file.getvalue())
        )

        assert write_row.mock_calls[1][1][1]["foo_reference"].id == 1
        assert write_row.mock_calls[3][1][1]["foo_reference"].id == 2

    @mock.patch("snowfakery.output_streams.DebugOutputStream.write_row")
    def test_ids_go_up(self, write_row):
        yaml = """
            - object: foo
              count: 5
              nickname: Foo
            """
        continuation_file = StringIO()
        generate(StringIO(yaml), generate_continuation_file=continuation_file)
        generate(
            StringIO(yaml), continuation_file=StringIO(continuation_file.getvalue())
        )

        assert write_row.mock_calls[-1][1][1]["id"] == 10

    @mock.patch("snowfakery.output_streams.DebugOutputStream.write_row")
    def test_faker_dates_work(self, write_row):
        yaml = """
            - object: foo
              count: 50
              fields:
                a_date:
                    date_between:
                        start_date: -30d
                        end_date: +180d
            """
        continuation_file = StringIO()
        generate(StringIO(yaml), generate_continuation_file=continuation_file)
        assert "a_date" in continuation_file.getvalue()
