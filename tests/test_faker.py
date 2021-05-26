from io import StringIO
from unittest import mock
from datetime import date

import pytest

from snowfakery.data_generator import generate
from snowfakery import data_gen_exceptions as exc

write_row_path = "snowfakery.output_streams.DebugOutputStream.write_row"


def row_values(write_row_mock, index, value):
    return write_row_mock.mock_calls[index][1][1][value]


class TestFaker:
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
    def test_fake_inline_overrides(self, write_row_mock):
        yaml = """
        - object: OBJ
          fields:
            name: ${{fake.FirstName}} ${{fake.LastName}}
        """
        generate(StringIO(yaml), {}, None)
        assert len(row_values(write_row_mock, 0, "name").split(" ")) == 2

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

    @mock.patch(write_row_path)
    def test_snowfakery_names(self, write_row_mock):
        yaml = """
        - object: A
          fields:
            fn:
              fake: FirstName
            ln:
              fake: LastName
            un:
              fake: UserNAME
            un2:
              fake: username
            alias:
              fake: Alias
            email:
              fake: Email
            danger_mail:
              fake: RealisticMaybeRealEmail
            email2:
              fake: email
        """
        generate(StringIO(yaml), {}, None)
        assert "_" in row_values(write_row_mock, 0, "un")
        assert "@" in row_values(write_row_mock, 0, "un2")
        assert len(row_values(write_row_mock, 0, "alias")) <= 8
        assert "@example" in row_values(write_row_mock, 0, "email")
        assert "@" in row_values(write_row_mock, 0, "email2")
        assert "@" in row_values(write_row_mock, 0, "danger_mail")

    @mock.patch(write_row_path)
    def test_fallthrough_to_faker(self, write_row_mock):
        yaml = """
        - object: A
          fields:
            SSN:
              fake: ssn
        """
        generate(StringIO(yaml), {}, None)
        assert row_values(write_row_mock, 0, "SSN")

    @mock.patch(write_row_path)
    def test_faker_kwargs(self, write_row_mock):
        yaml = """
        - object: A
          fields:
            neg:
              fake.random_int:
                min: -5
                max: -1
        """
        generate(StringIO(yaml), {}, None)
        assert -5 <= row_values(write_row_mock, 0, "neg") <= -1

    @mock.patch(write_row_path)
    def test_error_handling(self, write_row_mock):
        yaml = """
        - object: A
          fields:
            xyzzy:
              fake: xyzzy
        """
        with pytest.raises(exc.DataGenError) as e:
            generate(StringIO(yaml), {}, None)
        assert "xyzzy" in str(e.value)
        assert "fake" in str(e.value)
