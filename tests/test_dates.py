from io import StringIO


class TestDates:
    def test_date_math(self, generate, generated_rows):
        yaml = """
        - object: OBJ
          fields:
            basedate: ${{datetime(year=2000, month=1, day=1)}}
            dateplus: ${{basedate + relativedelta(years=22)}}
        """
        generate(StringIO(yaml), {})
        date = generated_rows.table_values("OBJ", 1, "dateplus")
        assert date.year == 2022
        assert date.month == 1
        assert date.day == 1
