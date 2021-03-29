from io import StringIO
import unittest
from unittest import mock
from datetime import date

import pytest

from snowfakery.data_generator import generate

write_row_path = "snowfakery.output_streams.DebugOutputStream.write_row"


def row_values(write_row_mock, index, value):
    return write_row_mock.mock_calls[index][1][1][value]


class TestFaker(unittest.TestCase):
    @mock.patch(write_row_path)
    def test_fake_block_simple(self, write_row_mock):
        yaml = """
        - object: OBJ
          fields:
            first_name:
                fake:
                    first_name
        """
        generate(StringIO(yaml), {}, None)
        assert row_values(write_row_mock, 0, "first_name")

    @mock.patch(write_row_path)
    def test_fake_block_simple_oneline(self, write_row_mock):
        yaml = """
        - object: OBJ
          fields:
            first_name:
                fake: first_name
        """
        generate(StringIO(yaml), {}, None)
        assert row_values(write_row_mock, 0, "first_name")

    @mock.patch(write_row_path)
    def test_fake_block_one_param(self, write_row_mock):
        yaml = """
        - object: OBJ
          fields:
            country:
                fake.country_code:
                    representation: alpha-2
        """
        generate(StringIO(yaml), {})
        assert len(row_values(write_row_mock, 0, "country")) == 2

    @mock.patch(write_row_path)
    def test_fake_inline(self, write_row_mock):
        yaml = """
        - object: OBJ
          fields:
            country: ${{fake.country_code(representation='alpha-2')}}
        """
        generate(StringIO(yaml), {}, None)
        assert len(row_values(write_row_mock, 0, "country")) == 2

    @mock.patch(write_row_path)
    def test_fake_two_params_flat(self, write_row_mock):
        yaml = """
        - object: OBJ
          fields:
            date: ${{fake.date(pattern="%Y-%m-%d", end_datetime=None)}}
        """
        generate(StringIO(yaml), {}, None)
        date = row_values(write_row_mock, 0, "date")
        assert type(date) == str, write_row_mock.mock_calls
        assert len(date.split("-")) == 3, date

    @mock.patch(write_row_path)
    def test_fake_two_params_nested(self, write_row_mock):
        yaml = """
        - object: OBJ
          fields:
            date:
                fake.date_between:
                    start_date: -10y
                    end_date: today
        """
        generate(StringIO(yaml), {}, None)
        assert row_values(write_row_mock, 0, "date").year

    @pytest.mark.skipif("os.environ.get('SNOWFAKERY_DETERMINISTIC_FAKE')")
    @mock.patch(write_row_path)
    def test_non_overlapping_dates(self, write_row_mock):
        yaml = """
        - object: OBJ
          fields:
            date:
                date_between:
                    start_date: today
                    end_date: 2000-01-01
        """
        generate(StringIO(yaml), {}, None)
        assert row_values(write_row_mock, 0, "date") is None

    @mock.patch(write_row_path)
    def test_months_past(self, write_row_mock):
        yaml = """
        - object: A
          fields:
            date:
              date_between:
                start_date: -4M
                end_date: -3M
        """
        generate(StringIO(yaml), {}, None)
        the_date = row_values(write_row_mock, 0, "date")
        assert (date.today() - the_date).days > 80
        assert (date.today() - the_date).days < 130
