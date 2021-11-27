from io import StringIO
from snowfakery import generate_data


class TestDates:
    def test_date_math(self, generated_rows):
        yaml = """
        - object: OBJ
          fields:
            basedate: ${{datetime(year=2000, month=1, day=1)}}
            dateplus: ${{basedate + relativedelta(years=22)}}
        """
        generate_data(StringIO(yaml))
        date = generated_rows.table_values("OBJ", 1, "dateplus")
        assert date.year == 2022
        assert date.month == 1
        assert date.day == 1
