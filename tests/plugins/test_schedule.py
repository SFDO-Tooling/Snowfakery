from io import StringIO

import pytest

from snowfakery.api import generate_data
import snowfakery.data_gen_exceptions as exc
from snowfakery.data_generator_runtime_object_model import StructuredValue
from snowfakery.recipe_validator import ValidationContext
from snowfakery.standard_plugins.Schedule import Schedule


class TestScheduleFunctions:
    """Test Schedule plugin runtime functionality"""

    def test_event_basic(self, generated_rows):
        """Test basic Schedule.Event usage"""
        yaml = """
        - plugin: snowfakery.standard_plugins.Schedule
        - object: Meeting
          count: 3
          fields:
            Date:
              Schedule.Event:
                start_date: 2023-01-01
                freq: weekly
        """
        generate_data(StringIO(yaml))
        assert generated_rows.row_values(0, "Date") is not None
        assert generated_rows.row_values(1, "Date") is not None


class TestScheduleValidator:
    """Test validators for Schedule.Event()"""

    def test_valid_default(self):
        """Test valid call with required freq only"""
        context = ValidationContext()
        sv = StructuredValue("Schedule.Event", {"freq": "weekly"}, "test.yml", 10)

        Schedule.Validators.validate_Event(sv, context)

        assert len(context.errors) == 0
        assert len(context.warnings) == 0

    def test_valid_all_frequencies(self):
        """Test all valid frequency values"""
        valid_freqs = [
            "YEARLY",
            "MONTHLY",
            "WEEKLY",
            "DAILY",
            "HOURLY",
            "MINUTELY",
            "SECONDLY",
        ]

        for freq in valid_freqs:
            context = ValidationContext()
            sv = StructuredValue("Schedule.Event", {"freq": freq}, "test.yml", 10)

            Schedule.Validators.validate_Event(sv, context)

            assert len(context.errors) == 0, f"Frequency {freq} should be valid"

    def test_valid_case_insensitive_freq(self):
        """Test frequency is case-insensitive"""
        for freq in ["weekly", "Weekly", "WEEKLY", "WeeKLY"]:
            context = ValidationContext()
            sv = StructuredValue("Schedule.Event", {"freq": freq}, "test.yml", 10)

            Schedule.Validators.validate_Event(sv, context)

            assert len(context.errors) == 0

    def test_valid_with_all_params(self):
        """Test valid call with all documented parameters"""
        context = ValidationContext()
        sv = StructuredValue(
            "Schedule.Event",
            {
                "freq": "monthly",
                "start_date": "2024-01-01",
                "interval": 2,
                "count": 10,
                "bymonthday": 1,
                "byweekday": "MO",
                "byhour": 9,
                "byminute": 0,
                "bysecond": 0,
            },
            "test.yml",
            10,
        )

        Schedule.Validators.validate_Event(sv, context)

        assert len(context.errors) == 0

    def test_missing_freq(self):
        """Test error when freq parameter is missing"""
        context = ValidationContext()
        sv = StructuredValue("Schedule.Event", {}, "test.yml", 10)

        Schedule.Validators.validate_Event(sv, context)

        assert len(context.errors) >= 1
        assert any(
            "missing" in err.message.lower() and "freq" in err.message.lower()
            for err in context.errors
        )

    def test_invalid_freq_string(self):
        """Test error when freq is invalid"""
        context = ValidationContext()
        sv = StructuredValue("Schedule.Event", {"freq": "biweekly"}, "test.yml", 10)

        Schedule.Validators.validate_Event(sv, context)

        assert len(context.errors) >= 1
        assert any("invalid frequency" in err.message.lower() for err in context.errors)

    def test_invalid_freq_type(self):
        """Test error when freq is not a string"""
        context = ValidationContext()
        sv = StructuredValue("Schedule.Event", {"freq": 123}, "test.yml", 10)

        Schedule.Validators.validate_Event(sv, context)

        assert len(context.errors) >= 1
        assert any(
            "freq" in err.message.lower() and "string" in err.message.lower()
            for err in context.errors
        )

    def test_invalid_start_date_type(self):
        """Test error when start_date is invalid type"""
        context = ValidationContext()
        sv = StructuredValue(
            "Schedule.Event", {"freq": "weekly", "start_date": 123}, "test.yml", 10
        )

        Schedule.Validators.validate_Event(sv, context)

        assert len(context.errors) >= 1
        assert any("start_date" in err.message.lower() for err in context.errors)

    def test_invalid_interval_zero(self):
        """Test error when interval is zero"""
        context = ValidationContext()
        sv = StructuredValue(
            "Schedule.Event", {"freq": "weekly", "interval": 0}, "test.yml", 10
        )

        Schedule.Validators.validate_Event(sv, context)

        assert len(context.errors) >= 1
        assert any(
            "interval" in err.message.lower() and "positive" in err.message.lower()
            for err in context.errors
        )

    def test_invalid_interval_negative(self):
        """Test error when interval is negative"""
        context = ValidationContext()
        sv = StructuredValue(
            "Schedule.Event", {"freq": "weekly", "interval": -1}, "test.yml", 10
        )

        Schedule.Validators.validate_Event(sv, context)

        assert len(context.errors) >= 1
        assert any(
            "interval" in err.message.lower() and "positive" in err.message.lower()
            for err in context.errors
        )

    def test_invalid_interval_type(self):
        """Test error when interval is not an integer"""
        context = ValidationContext()
        sv = StructuredValue(
            "Schedule.Event", {"freq": "weekly", "interval": "2"}, "test.yml", 10
        )

        Schedule.Validators.validate_Event(sv, context)

        assert len(context.errors) >= 1
        assert any(
            "interval" in err.message.lower() and "integer" in err.message.lower()
            for err in context.errors
        )

    def test_invalid_count_zero(self):
        """Test error when count is zero"""
        context = ValidationContext()
        sv = StructuredValue(
            "Schedule.Event", {"freq": "weekly", "count": 0}, "test.yml", 10
        )

        Schedule.Validators.validate_Event(sv, context)

        assert len(context.errors) >= 1
        assert any(
            "count" in err.message.lower() and "positive" in err.message.lower()
            for err in context.errors
        )

    def test_invalid_count_type(self):
        """Test error when count is not an integer"""
        context = ValidationContext()
        sv = StructuredValue(
            "Schedule.Event", {"freq": "weekly", "count": "10"}, "test.yml", 10
        )

        Schedule.Validators.validate_Event(sv, context)

        assert len(context.errors) >= 1
        assert any(
            "count" in err.message.lower() and "integer" in err.message.lower()
            for err in context.errors
        )

    def test_invalid_until_type(self):
        """Test error when until is invalid type"""
        context = ValidationContext()
        sv = StructuredValue(
            "Schedule.Event", {"freq": "weekly", "until": 123}, "test.yml", 10
        )

        Schedule.Validators.validate_Event(sv, context)

        assert len(context.errors) >= 1
        assert any("until" in err.message.lower() for err in context.errors)

    def test_warning_count_and_until(self):
        """Test warning when both count and until provided"""
        context = ValidationContext()
        sv = StructuredValue(
            "Schedule.Event",
            {"freq": "weekly", "count": 10, "until": "2025-12-31"},
            "test.yml",
            10,
        )

        Schedule.Validators.validate_Event(sv, context)

        assert len(context.warnings) >= 1
        assert any(
            "count" in warn.message.lower() and "until" in warn.message.lower()
            for warn in context.warnings
        )

    def test_valid_byweekday(self):
        """Test valid weekday values"""
        valid_weekdays = ["MO", "TU", "WE", "TH", "FR", "SA", "SU"]

        for weekday in valid_weekdays:
            context = ValidationContext()
            sv = StructuredValue(
                "Schedule.Event",
                {"freq": "weekly", "byweekday": weekday},
                "test.yml",
                10,
            )

            Schedule.Validators.validate_Event(sv, context)

            assert len(context.errors) == 0, f"Weekday {weekday} should be valid"

    def test_valid_byweekday_multiple(self):
        """Test valid multiple weekdays"""
        context = ValidationContext()
        sv = StructuredValue(
            "Schedule.Event",
            {"freq": "weekly", "byweekday": "MO, WE, FR"},
            "test.yml",
            10,
        )

        Schedule.Validators.validate_Event(sv, context)

        assert len(context.errors) == 0

    def test_valid_byweekday_with_offset(self):
        """Test valid weekday with offset"""
        context = ValidationContext()
        sv = StructuredValue(
            "Schedule.Event", {"freq": "monthly", "byweekday": "MO(+1)"}, "test.yml", 10
        )

        Schedule.Validators.validate_Event(sv, context)

        assert len(context.errors) == 0

    def test_invalid_byweekday(self):
        """Test error when weekday is invalid"""
        context = ValidationContext()
        sv = StructuredValue(
            "Schedule.Event", {"freq": "weekly", "byweekday": "XX"}, "test.yml", 10
        )

        Schedule.Validators.validate_Event(sv, context)

        assert len(context.errors) >= 1
        assert any("invalid weekday" in err.message.lower() for err in context.errors)

    def test_invalid_byweekday_type(self):
        """Test error when byweekday is not a string"""
        context = ValidationContext()
        sv = StructuredValue(
            "Schedule.Event", {"freq": "weekly", "byweekday": 1}, "test.yml", 10
        )

        Schedule.Validators.validate_Event(sv, context)

        assert len(context.errors) >= 1
        assert any(
            "byweekday" in err.message.lower() and "string" in err.message.lower()
            for err in context.errors
        )

    def test_valid_bymonthday(self):
        """Test valid bymonthday values"""
        context = ValidationContext()
        sv = StructuredValue(
            "Schedule.Event", {"freq": "monthly", "bymonthday": 15}, "test.yml", 10
        )

        Schedule.Validators.validate_Event(sv, context)

        assert len(context.errors) == 0

    def test_valid_bymonthday_negative(self):
        """Test valid negative bymonthday (last day)"""
        context = ValidationContext()
        sv = StructuredValue(
            "Schedule.Event", {"freq": "monthly", "bymonthday": -1}, "test.yml", 10
        )

        Schedule.Validators.validate_Event(sv, context)

        assert len(context.errors) == 0

    def test_valid_bymonthday_string(self):
        """Test valid bymonthday as comma-separated string"""
        context = ValidationContext()
        sv = StructuredValue(
            "Schedule.Event",
            {"freq": "monthly", "bymonthday": "1, 15, -1"},
            "test.yml",
            10,
        )

        Schedule.Validators.validate_Event(sv, context)

        assert len(context.errors) == 0

    def test_invalid_bymonthday_zero(self):
        """Test error when bymonthday is zero"""
        context = ValidationContext()
        sv = StructuredValue(
            "Schedule.Event", {"freq": "monthly", "bymonthday": 0}, "test.yml", 10
        )

        Schedule.Validators.validate_Event(sv, context)

        assert len(context.errors) >= 1
        assert any(
            "bymonthday" in err.message.lower() and "cannot be 0" in err.message.lower()
            for err in context.errors
        )

    def test_invalid_bymonthday_out_of_range(self):
        """Test error when bymonthday is out of range"""
        context = ValidationContext()
        sv = StructuredValue(
            "Schedule.Event", {"freq": "monthly", "bymonthday": 32}, "test.yml", 10
        )

        Schedule.Validators.validate_Event(sv, context)

        assert len(context.errors) >= 1
        assert any("bymonthday" in err.message.lower() for err in context.errors)

    def test_invalid_bymonthday_string_format(self):
        """Test error when bymonthday string contains non-integers"""
        context = ValidationContext()
        sv = StructuredValue(
            "Schedule.Event",
            {"freq": "monthly", "bymonthday": "1, abc, 15"},
            "test.yml",
            10,
        )

        Schedule.Validators.validate_Event(sv, context)

        assert len(context.errors) >= 1
        assert any(
            "bymonthday" in err.message.lower() and "integers" in err.message.lower()
            for err in context.errors
        )

    def test_invalid_bymonthday_type(self):
        """Test error when bymonthday is invalid type (dict)"""
        context = ValidationContext()
        sv = StructuredValue(
            "Schedule.Event",
            {"freq": "monthly", "bymonthday": {"key": "value"}},
            "test.yml",
            10,
        )

        Schedule.Validators.validate_Event(sv, context)

        assert len(context.errors) >= 1
        assert any("bymonthday" in err.message.lower() for err in context.errors)

    def test_valid_byyearday(self):
        """Test valid byyearday values"""
        context = ValidationContext()
        sv = StructuredValue(
            "Schedule.Event", {"freq": "yearly", "byyearday": 100}, "test.yml", 10
        )

        Schedule.Validators.validate_Event(sv, context)

        assert len(context.errors) == 0

    def test_invalid_byyearday_zero(self):
        """Test error when byyearday is zero"""
        context = ValidationContext()
        sv = StructuredValue(
            "Schedule.Event", {"freq": "yearly", "byyearday": 0}, "test.yml", 10
        )

        Schedule.Validators.validate_Event(sv, context)

        assert len(context.errors) >= 1
        assert any("byyearday" in err.message.lower() for err in context.errors)

    def test_valid_byhour(self):
        """Test valid byhour values"""
        context = ValidationContext()
        sv = StructuredValue(
            "Schedule.Event", {"freq": "daily", "byhour": 9}, "test.yml", 10
        )

        Schedule.Validators.validate_Event(sv, context)

        assert len(context.errors) == 0

    def test_valid_byhour_string(self):
        """Test valid byhour as comma-separated string"""
        context = ValidationContext()
        sv = StructuredValue(
            "Schedule.Event", {"freq": "daily", "byhour": "9, 12, 15"}, "test.yml", 10
        )

        Schedule.Validators.validate_Event(sv, context)

        assert len(context.errors) == 0

    def test_invalid_byhour_out_of_range(self):
        """Test error when byhour is out of range"""
        context = ValidationContext()
        sv = StructuredValue(
            "Schedule.Event", {"freq": "daily", "byhour": 24}, "test.yml", 10
        )

        Schedule.Validators.validate_Event(sv, context)

        assert len(context.errors) >= 1
        assert any("byhour" in err.message.lower() for err in context.errors)

    def test_invalid_byhour_negative(self):
        """Test error when byhour is negative"""
        context = ValidationContext()
        sv = StructuredValue(
            "Schedule.Event", {"freq": "daily", "byhour": -1}, "test.yml", 10
        )

        Schedule.Validators.validate_Event(sv, context)

        assert len(context.errors) >= 1
        assert any("byhour" in err.message.lower() for err in context.errors)

    def test_invalid_byhour_string_format(self):
        """Test error when byhour string contains non-integers"""
        context = ValidationContext()
        sv = StructuredValue(
            "Schedule.Event", {"freq": "daily", "byhour": "9, abc, 15"}, "test.yml", 10
        )

        Schedule.Validators.validate_Event(sv, context)

        assert len(context.errors) >= 1
        assert any(
            "byhour" in err.message.lower() and "integers" in err.message.lower()
            for err in context.errors
        )

    def test_invalid_byhour_type(self):
        """Test error when byhour is invalid type (dict)"""
        context = ValidationContext()
        sv = StructuredValue(
            "Schedule.Event",
            {"freq": "daily", "byhour": {"key": "value"}},
            "test.yml",
            10,
        )

        Schedule.Validators.validate_Event(sv, context)

        assert len(context.errors) >= 1
        assert any("byhour" in err.message.lower() for err in context.errors)

    def test_valid_byminute(self):
        """Test valid byminute values"""
        context = ValidationContext()
        sv = StructuredValue(
            "Schedule.Event", {"freq": "hourly", "byminute": 30}, "test.yml", 10
        )

        Schedule.Validators.validate_Event(sv, context)

        assert len(context.errors) == 0

    def test_invalid_byminute_out_of_range(self):
        """Test error when byminute is out of range"""
        context = ValidationContext()
        sv = StructuredValue(
            "Schedule.Event", {"freq": "hourly", "byminute": 60}, "test.yml", 10
        )

        Schedule.Validators.validate_Event(sv, context)

        assert len(context.errors) >= 1
        assert any("byminute" in err.message.lower() for err in context.errors)

    def test_valid_bysecond(self):
        """Test valid bysecond values"""
        context = ValidationContext()
        sv = StructuredValue(
            "Schedule.Event", {"freq": "minutely", "bysecond": 30}, "test.yml", 10
        )

        Schedule.Validators.validate_Event(sv, context)

        assert len(context.errors) == 0

    def test_invalid_bysecond_out_of_range(self):
        """Test error when bysecond is out of range"""
        context = ValidationContext()
        sv = StructuredValue(
            "Schedule.Event", {"freq": "minutely", "bysecond": 60}, "test.yml", 10
        )

        Schedule.Validators.validate_Event(sv, context)

        assert len(context.errors) >= 1
        assert any("bysecond" in err.message.lower() for err in context.errors)

    def test_valid_exclude_date(self):
        """Test valid exclude with date string"""
        context = ValidationContext()
        sv = StructuredValue(
            "Schedule.Event",
            {"freq": "daily", "exclude": "2025-05-01"},
            "test.yml",
            10,
        )

        Schedule.Validators.validate_Event(sv, context)

        assert len(context.errors) == 0

    def test_valid_include_date(self):
        """Test valid include with date string"""
        context = ValidationContext()
        sv = StructuredValue(
            "Schedule.Event",
            {"freq": "monthly", "include": "2025-02-14"},
            "test.yml",
            10,
        )

        Schedule.Validators.validate_Event(sv, context)

        assert len(context.errors) == 0

    def test_invalid_exclude_type(self):
        """Test error when exclude is invalid type"""
        context = ValidationContext()
        sv = StructuredValue(
            "Schedule.Event",
            {"freq": "daily", "exclude": 123},
            "test.yml",
            10,
        )

        Schedule.Validators.validate_Event(sv, context)

        assert len(context.errors) >= 1
        assert any("exclude" in err.message.lower() for err in context.errors)

    def test_invalid_exclude_list_item_type(self):
        """Test error when exclude list contains invalid item type"""
        context = ValidationContext()
        # Create a mock list with integer item
        sv = StructuredValue(
            "Schedule.Event",
            {"freq": "daily", "exclude": ["2025-01-01", 123]},
            "test.yml",
            10,
        )

        Schedule.Validators.validate_Event(sv, context)

        assert len(context.errors) >= 1
        assert any("exclude" in err.message.lower() for err in context.errors)

    def test_warning_exclude_wrong_function(self):
        """Test warning when exclude uses wrong function"""
        context = ValidationContext()
        # Create nested StructuredValue with wrong function
        wrong_func = StructuredValue("SomeOtherFunction", {}, "test.yml", 11)
        sv = StructuredValue(
            "Schedule.Event",
            {"freq": "daily", "exclude": wrong_func},
            "test.yml",
            10,
        )

        Schedule.Validators.validate_Event(sv, context)

        assert len(context.warnings) >= 1
        assert any("exclude" in warn.message.lower() for warn in context.warnings)

    def test_warning_exclude_list_wrong_function(self):
        """Test warning when exclude list contains wrong function"""
        context = ValidationContext()
        wrong_func = StructuredValue("SomeOtherFunction", {}, "test.yml", 11)
        sv = StructuredValue(
            "Schedule.Event",
            {"freq": "daily", "exclude": [wrong_func]},
            "test.yml",
            10,
        )

        Schedule.Validators.validate_Event(sv, context)

        assert len(context.warnings) >= 1
        assert any("exclude" in warn.message.lower() for warn in context.warnings)

    def test_unknown_parameter_warning(self):
        """Test warning for unknown parameters"""
        context = ValidationContext()
        sv = StructuredValue(
            "Schedule.Event",
            {"freq": "weekly", "unknown_param": "value"},
            "test.yml",
            10,
        )

        Schedule.Validators.validate_Event(sv, context)

        assert len(context.warnings) >= 1
        assert any(
            "unknown parameter" in warn.message.lower() for warn in context.warnings
        )

    def test_jinja_schedule_valid(self):
        """Test Schedule.Event used as field value"""
        yaml = """
        - plugin: snowfakery.standard_plugins.Schedule
        - object: Meeting
          count: 3
          fields:
            EventDate:
              Schedule.Event:
                freq: weekly
                start_date: 2024-01-01
                count: 5
        """
        result = generate_data(StringIO(yaml), validate_only=True)
        assert result.errors == []

    def test_jinja_schedule_invalid_freq(self):
        """Test Schedule.Event with invalid freq in Jinja"""
        yaml = """
        - plugin: snowfakery.standard_plugins.Schedule
        - var: events
          value:
            Schedule.Event:
              freq: invalid
        """
        with pytest.raises(exc.DataGenValidationError) as e:
            generate_data(StringIO(yaml), validate_only=True)
        assert "freq" in str(e.value).lower()


class TestScheduleValidationIntegration:
    """Integration tests for Schedule validation"""

    def test_schedule_with_multiple_params(self):
        """Test Schedule.Event with multiple parameters"""
        yaml = """
        - plugin: snowfakery.standard_plugins.Schedule
        - object: WeeklyMeeting
          count: 5
          fields:
            EventDate:
              Schedule.Event:
                freq: weekly
                start_date: 2024-01-01
                interval: 2
                byweekday: "MO, WE, FR"
                byhour: 9
                byminute: 30
        """
        result = generate_data(StringIO(yaml), validate_only=True)
        assert result.errors == []

    def test_multiple_errors(self):
        """Test multiple validation errors are caught"""
        yaml = """
        - plugin: snowfakery.standard_plugins.Schedule
        - var: bad_event
          value:
            Schedule.Event:
              freq: invalid
              interval: 0
              count: 0
        """
        with pytest.raises(exc.DataGenValidationError) as e:
            generate_data(StringIO(yaml), validate_only=True)
        # Should catch multiple errors
        assert "freq" in str(e.value).lower() or "interval" in str(e.value).lower()
