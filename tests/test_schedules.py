from pathlib import Path
from snowfakery.data_generator import generate
from io import StringIO
from datetime import date, datetime, timezone
import pytest
import snowfakery.data_gen_exceptions as exc
from snowfakery.output_streams import DebugOutputStream


def dt(*args):
    return datetime(*args, tzinfo=timezone.utc)


def test_simple(generated_rows):
    sample = "examples/schedule/weekly.recipe.yml"
    with open(sample) as f:
        generate(f)
    vals = generated_rows.table_values("WeeklyEvents", field="WeeklyEvent")
    assert vals == [
        date(2024, 1, 1),
        date(2024, 1, 8),
        date(2024, 1, 15),
    ]


def test_inclusions(generated_rows):
    sample = "examples/schedule/inclusions.recipe.yml"
    with open(sample) as f:
        generate(f)
    assert generated_rows.table_values(
        "MonthlyEventsPlusValentines", field="MonthlyEvent"
    ) == [
        date(2025, 2, 1),
        date(2025, 2, 14),  # valentines
        date(2025, 3, 1),
        date(2025, 4, 1),
        date(2025, 5, 1),
        date(2025, 6, 1),
        date(2025, 7, 1),
        date(2025, 8, 1),
        date(2025, 9, 1),
        date(2025, 10, 1),
    ]

    assert (
        generated_rows.table_values(
            "MonthlyEventsPlusSeveralNewYears", field="MonthlyEvent"
        )
    ) == [
        date(2000, 1, 1),  # New Years
        date(2001, 1, 1),  # New Years
        date(2002, 1, 1),  # New Years
        date(2025, 2, 1),
        date(2025, 3, 1),
        date(2025, 4, 1),
        date(2025, 5, 1),
        date(2025, 6, 1),
        date(2025, 7, 1),
        date(2025, 8, 1),
    ]


def test_exclusions_simple(generated_rows):
    sample = "examples/schedule/exclusions_no_May.recipe.yml"
    with open(sample) as f:
        generate(f)
    vals = generated_rows.table_values("MonthlyEventsExceptMay", field="MonthlyEvent")
    assert vals == [
        date(2025, 2, 1),
        date(2025, 3, 1),
        date(2025, 4, 1),
        date(2025, 6, 1),  # May is missing here
        date(2025, 7, 1),
        date(2025, 8, 1),
        date(2025, 9, 1),
        date(2025, 10, 1),
        date(2025, 11, 1),
        date(2025, 12, 1),
        date(2026, 1, 1),
        date(2026, 2, 1),
    ]


def test_exclusions_complex(generated_rows):
    sample = "examples/schedule/exclusions_no_summer.recipe.yml"
    with open(sample) as f:
        generate(f)

    vals = generated_rows.table_values(
        "MonthlyEventsExceptSummer", field="MonthlyEvent"
    )
    assert vals == [
        date(2025, 2, 1),
        date(2025, 3, 1),
        date(2025, 4, 1),  # next few (summer) months are missing
        date(2025, 9, 1),
        date(2025, 10, 1),
        date(2025, 11, 1),
        date(2025, 12, 1),
        date(2026, 1, 1),
        date(2026, 2, 1),
        date(2026, 3, 1),
    ]


def test_complex_exclusions(generated_rows):
    sample = "examples/schedule/complex_inclusions.recipe.yml"
    with open(sample) as f:
        generate(f)
    vals = generated_rows.table_values(
        "MonthlyEventsPlusValentinesPlusSeveralNewYears", field="MonthlyEvent"
    )
    assert vals == [
        date(2000, 1, 1),
        date(2001, 1, 1),
        date(2002, 1, 1),
        date(2025, 2, 1),
        date(2025, 2, 14),
        date(2025, 3, 1),
        date(2025, 4, 1),
        date(2025, 5, 1),
        date(2025, 6, 1),
        date(2025, 7, 1),
    ]


def test_default_start_date(generated_rows):
    yaml = """
    - plugin: snowfakery.standard_plugins.Schedule
    - object: WeeklyEvents
      count: 3
      fields:
        WeeklyEvent:
            Schedule.Event:
                freq: weekly
    """
    generate(StringIO(yaml))
    vals = generated_rows.table_values("WeeklyEvents", field="WeeklyEvent")
    assert len(vals) == 3
    vals[0].toordinal() == vals[1].toordinal() - 7 == vals[2].toordinal() - 14


def test_datetime_start_date(generated_rows):
    yaml = """
    - plugin: snowfakery.standard_plugins.Schedule
    - object: MinutelyEvents
      count: 3
      fields:
        MinutelyEvent:
            Schedule.Event:
                start_date: 2020-01-01 10:10:10
                freq: MINUTELY
    """
    generate(StringIO(yaml))
    vals = generated_rows.table_values("MinutelyEvents", field="MinutelyEvent")
    print(vals)
    assert [val.minute for val in vals] == [10, 11, 12]


def test_bad_start_date_type():
    yaml = """
    - plugin: snowfakery.standard_plugins.Schedule
    - object: MinutelyEvents
      count: 3
      fields:
        MinutelyEvent:
            Schedule.Event:
                start_date: True
                freq: MINUTELY
    """
    with pytest.raises(exc.DataGenError) as e:
        generate(StringIO(yaml))
    assert "start_date" in str(e.value)


def test_bad_include():
    yaml = """
    - plugin: snowfakery.standard_plugins.Schedule
    - object: MinutelyEvents
      count: 3
      fields:
        MinutelyEvent:
            Schedule.Event:
                freq: MINUTELY
                include: True
    """
    with pytest.raises(exc.DataGenError) as e:
        generate(StringIO(yaml))
    assert "include" in str(e.value)


def test_bad_frequency():
    yaml = """
    - plugin: snowfakery.standard_plugins.Schedule
    - object: MinutelyEvents
      count: 3
      fields:
        MinutelyEvent:
            Schedule.Event:
                freq: BLAH
    """
    with pytest.raises(exc.DataGenError) as e:
        generate(StringIO(yaml))
    assert "frequency" in str(e.value)


def test_datetime_types_inferred_from_start_date(generated_rows):
    with open("examples/schedule/haunting.recipe.yml") as yaml:
        generate(yaml)
    vals = generated_rows.table_values("ScaryEvent", field="DateTime")
    print(vals)
    assert isinstance(vals[0], datetime)
    assert vals == [
        dt(2023, 10, 31, 23, 59, 59),
        dt(2024, 10, 31, 23, 59, 59),
        dt(2025, 10, 31, 23, 59, 59),
        dt(2026, 10, 31, 23, 59, 59),
        dt(2027, 10, 31, 23, 59, 59),
    ], vals


def test_hourly_secondly_etc_require_datetime_start_date():
    yaml = """
    - plugin: snowfakery.standard_plugins.Schedule
    - object: FrequentEvent
      count: 3
      fields:
        DateTime:
            Schedule.Event:
                start_date: 2000-01-01
                freq: Minutely
    """
    with pytest.raises(exc.DataGenError) as e:
        generate(StringIO(yaml))
    assert "start_date" in str(e.value)

    yaml2 = yaml.replace("Minutely", "Hourly")

    with pytest.raises(exc.DataGenError) as e:
        generate(StringIO(yaml2))
    assert "start_date" in str(e.value)

    yaml3 = yaml.replace("Minutely", "Secondly")

    with pytest.raises(exc.DataGenError) as e:
        generate(StringIO(yaml3))
    assert "start_date" in str(e.value)


def test_second_count(generated_rows):
    with open("examples/schedule/secondly.recipe.yml") as yaml:
        generate(yaml)
    vals = generated_rows.table_values("Seconds", field="DateTime")
    assert isinstance(vals[0], datetime)
    assert vals[0].tzinfo is timezone.utc
    assert vals == [
        dt(2023, 10, 31, 10, 10, 58),
        dt(2023, 10, 31, 10, 10, 59),
        dt(2023, 10, 31, 10, 11),
        dt(2023, 10, 31, 10, 11, 1),
        dt(2023, 10, 31, 10, 11, 2),
    ], vals


def test_every_other_monday_wednesday_friday(generated_rows):
    with open("examples/schedule/monday_wednesday_friday.recipe.yml") as yaml:
        generate(yaml)
    vals = generated_rows.table_values("Meeting", field="Date")
    assert vals == [
        date(2023, 1, 2),
        date(2023, 1, 4),
        date(2023, 1, 6),
        date(2023, 1, 9),
        date(2023, 1, 11),
    ]


def test_not_enough_dates():
    yaml = """
    - plugin: snowfakery.standard_plugins.Schedule
    - object: FrequentEvent
      count: 4
      fields:
        DateTime:
            Schedule.Event:
                start_date: 2000-01-01
                freq: Weekly
                count: 3
    """
    with pytest.raises(exc.DataGenError, match="Could not generate enough values"):
        generate(StringIO(yaml))


def test_parse_until_string__datetime(generated_rows):
    yaml = """
    - plugin: snowfakery.standard_plugins.Schedule
    - object: FrequentEvent
      count: 2
      fields:
        DateTime:
            Schedule.Event:
                start_date: 2000-01-01
                freq: Weekly
                until: "2000-01-20T12:12:01"
    """
    generate(StringIO(yaml))
    vals = generated_rows.table_values("FrequentEvent", field="DateTime")
    assert vals == [date(2000, 1, 1), date(2000, 1, 8)]


def test_parse_until_string__date(generated_rows):
    yaml = """
    - plugin: snowfakery.standard_plugins.Schedule
    - object: FrequentEvent
      count: 2
      fields:
        DateTime:
            Schedule.Event:
                start_date: 2000-01-01
                freq: Weekly
                until: "2000-01-20"
    """
    generate(StringIO(yaml))
    vals = generated_rows.table_values("FrequentEvent", field="DateTime")
    assert vals == [date(2000, 1, 1), date(2000, 1, 8)]


def test_parse_until__wrong_type(disable_typeguard):
    yaml = """
    - plugin: snowfakery.standard_plugins.Schedule
    - object: FrequentEvent
      count: 2
      fields:
        DateTime:
            Schedule.Event:
                start_date: 2000-01-01
                freq: Weekly
                until: True
    """
    with pytest.raises(exc.DataGenTypeError, match="True"):
        generate(StringIO(yaml))


def test_parse_byweekday__wrong_type(disable_typeguard):
    yaml = """
    - plugin: snowfakery.standard_plugins.Schedule
    - object: FrequentEvent
      count: 2
      fields:
        DateTime:
            Schedule.Event:
                start_date: 2000-01-01
                freq: Weekly
                byweekday: True
    """
    with pytest.raises(exc.DataGenTypeError, match="True"):
        generate(StringIO(yaml))


def test_parse_byweekday__wrong_string(disable_typeguard):
    yaml = """
    - plugin: snowfakery.standard_plugins.Schedule
    - object: FrequentEvent
      count: 2
      fields:
        DateTime:
            Schedule.Event:
                start_date: 2000-01-01
                freq: Weekly
                byweekday: JAN,FEB,MAR
    """
    with pytest.raises(exc.DataGenTypeError, match="JAN"):
        generate(StringIO(yaml))


def test_parse_byweekday__wrong_string__2(disable_typeguard):
    yaml = """
    - plugin: snowfakery.standard_plugins.Schedule
    - object: FrequentEvent
      count: 2
      fields:
        DateTime:
            Schedule.Event:
                start_date: 2000-01-01
                freq: Weekly
                byweekday: I_1Z_A_HA$0R(ABCDE)
    """
    with pytest.raises(exc.DataGenSyntaxError, match=r"I_1Z_A_HA"):
        generate(StringIO(yaml))


def test_parse_byweekday__bad_offset(disable_typeguard):
    yaml = """
    - plugin: snowfakery.standard_plugins.Schedule
    - object: FrequentEvent
      count: 2
      fields:
        DateTime:
            Schedule.Event:
                start_date: 2000-01-01
                freq: Weekly
                byweekday: MO(ABCDE)
    """
    with pytest.raises(exc.DataGenTypeError, match="ABCDE"):
        generate(StringIO(yaml))


def test_by_weekday_offsets(generated_rows):
    with open("examples/schedule/monday_wednesday_friday_monthly.recipe.yml") as f:
        generate(f)
    vals = generated_rows.table_values("Meeting", field="Date")
    print(vals)
    assert vals == [
        date(2023, 1, 2),
        date(2023, 1, 13),
        date(2023, 1, 25),
        date(2023, 2, 6),
        date(2023, 2, 10),
        date(2023, 2, 22),
        date(2023, 3, 6),
        date(2023, 3, 10),
        date(2023, 3, 29),
        date(2023, 4, 3),
    ]


infiles = [
    "examples/schedule/halloween.recipe.yml",
    "examples/schedule/haunting.recipe.yml",
    "examples/schedule/with_timezone.recipe.yml",
    "examples/schedule/secondly.recipe.yml",
    "examples/schedule/monday_wednesday_friday.recipe.yml",
    "examples/schedule/monday_wednesday_friday_monthly.recipe.yml",
    "examples/schedule/bymonthday.recipe.yml",
    "examples/schedule/byyearday.recipe.yml",
    "examples/schedule/bytimes.recipe.yml",
    "examples/schedule/every_third_week.recipe.yml",
    "examples/schedule/every_other_monday.recipe.yml",
    "examples/schedule/for_each_date.recipe.yml",
    "examples/schedule/inclusions.recipe.yml",
    "examples/schedule/deep_inclusions.yml",
    "examples/schedule/exclusions_no_May.recipe.yml",
    "examples/schedule/exclusions_no_summer.recipe.yml",
]


@pytest.mark.parametrize("filename", infiles)
def test_example_files(filename):
    f = StringIO()
    with open(filename) as yaml:
        generate(yaml, output_stream=DebugOutputStream(f))
    assert f.getvalue() == Path(filename.replace(".yml", ".out")).read_text()
