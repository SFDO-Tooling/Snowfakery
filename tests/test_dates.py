import pytest
from io import StringIO
from snowfakery import generate_data
from snowfakery import data_gen_exceptions as exc


class TestDates:
    def test_old_dates_as_strings(self, generated_rows):
        yaml = """
        - object: OBJ
          fields:
            basedate: ${{datetime(year=2000, month=1, day=1)}}
            dateplus: ${{basedate + "XYZZY"}}
        """
        generate_data(StringIO(yaml))
        date = generated_rows.table_values("OBJ", 1, "dateplus")
        assert date.startswith("2000")
        assert date.endswith("XYZZY")

    def test_date_math__native_types(self, generated_rows):
        yaml = """
        - object: OBJ
          fields:
            basedate: ${{datetime(year=2000, month=1, day=1)}}
            dateplus: ${{basedate + relativedelta(years=22)}}
        """
        generate_data(StringIO(yaml), plugin_options={"snowfakery_version": 3})
        date = generated_rows.table_values("OBJ", 1, "dateplus")
        assert str(date) == "2022-01-01 00:00:00+00:00"

    def test_date_math__native_types__error(self, generated_rows):
        yaml = """
        - object: OBJ
          fields:
            basedate: ${{datetime(year=2000, month=1, day=1)}}
            dateplus: ${{basedate + "XYZZY"}}
        """
        with pytest.raises(exc.DataGenValueError) as e:
            generate_data(StringIO(yaml), plugin_options={"snowfakery_version": 3})
        assert "dateplus" in str(e.value)

    def test_date_time__too_many_params__error(self):
        yaml = """
        - object: OBJ
          fields:
            basedate: ${{datetime("2022-01-01", year=2000, month=1, day=1)}}
            dateplus: ${{basedate + "XYZZY"}}
        """
        with pytest.raises(exc.DataGenValueError) as e:
            generate_data(StringIO(yaml), plugin_options={"snowfakery_version": 3})
        assert "date specification" in str(e.value)
