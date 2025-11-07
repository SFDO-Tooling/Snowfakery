from io import StringIO

import pytest

from snowfakery.api import generate_data
import snowfakery.data_gen_exceptions as exc
from snowfakery.data_generator_runtime_object_model import StructuredValue
from snowfakery.recipe_validator import ValidationContext
from snowfakery.standard_plugins.Counters import Counters


class TestCounter:
    def test_counter(self, generated_rows):
        with open("examples/counters/number_counter.recipe.yml") as f:
            generate_data(f)
        assert generated_rows.row_values(0, "count") == 1
        assert generated_rows.row_values(9, "count") == 10

    def test_counter_start(self, generated_rows):
        with open("examples/counters/counter_start.recipe.yml") as f:
            generate_data(f)
        assert generated_rows.row_values(0, "count") == 11
        assert generated_rows.row_values(9, "count") == 38

    def test_counter_iterations(self, generated_rows):
        with open("examples/counters/counter_start.recipe.yml") as f:
            generate_data(f, target_number=("Example", 20))
        assert generated_rows.row_values(0, "count") == 11
        assert generated_rows.row_values(9, "count") == 38
        # does not reset on iteration boundaries
        assert generated_rows.row_values(10, "count") == 41

    # counters should restart cleanly at continuation boundaries
    def test_counter_with_continuation(
        self, generate_data_with_continuation, generated_rows
    ):
        generate_data_with_continuation(
            yaml_file="examples/counters/number_counter.recipe.yml",
            target_number=("Example", 5),
            times=3,
        )
        assert generated_rows.row_values(0, "count") == 1
        assert generated_rows.row_values(10, "count") == 1
        assert generated_rows.row_values(29, "count") == 10

    def test_counter_in_variable(self, generated_rows):
        yaml = """
            - plugin: snowfakery.standard_plugins.Counters
            - var: my_counter
              value:
                Counters.NumberCounter:
            - object: Foo
              count: 10
              fields:
                counter: ${{my_counter.next()}}
        """
        generate_data(StringIO(yaml))
        assert generated_rows.table_values("Foo", 10, "counter") == 10


class TestDateCounter:
    # date counters do not reset on recipe iteration
    def test_date_counter(self, generated_rows):
        with open("examples/counters/date_counter.recipe.yml") as f:
            generate_data(f, target_number=("TV_Episode", 24))
        assert str(generated_rows.table_values("TV_Series", 1)["date"]) == "2021-12-12"
        assert str(generated_rows.table_values("TV_Episode", 1)["date"]) == "2021-12-12"
        assert str(generated_rows.table_values("TV_Series", 3)["date"]) == "2022-06-12"
        assert str(generated_rows.table_values("TV_Episode", 9)["date"]) == "2022-06-12"
        assert str(generated_rows.table_values("TV_Series", 4)["date"]) == "2022-09-11"
        assert str(generated_rows.table_values("TV_Series", 6)["date"]) == "2023-03-13"
        assert (
            str(generated_rows.table_values("TV_Episode", 21)["date"]) == "2023-03-13"
        )

    def test_date_counter_relative(self, generated_rows):
        yaml = """
          - plugin: snowfakery.standard_plugins.Counters
          - object: TV_Series
            count: 2
            fields:
              date:
                Counters.DateCounter:
                  start_date: today
                  step: +3M
        """
        generate_data(StringIO(yaml))
        start_date = generated_rows.row_values(0, "date")
        end_date = generated_rows.row_values(1, "date")
        delta = end_date - start_date
        assert 89 <= delta.days <= 91

    def test_date_start_date_error(self, generated_rows):
        yaml = """
          - plugin: snowfakery.standard_plugins.Counters
          - var: SeriesStarts
            value:
              Counters.DateCounter:
                start_date: xyzzy
                step: +3M
        """
        with pytest.raises(exc.DataGenError, match="xyzzy"):
            generate_data(StringIO(yaml))

    def test_counter_with_continuation(
        self, generate_data_with_continuation, generated_rows
    ):
        yaml = """
          - plugin: snowfakery.standard_plugins.Counters
          - object: TV_Series
            count: 2
            fields:
              date:
                Counters.DateCounter:
                  start_date: 2000-01-01
                  step: +1w
        """

        generate_data_with_continuation(
            yaml=yaml,
            target_number=("TV_Series", 5),
            times=3,
        )
        assert str(generated_rows.row_values(0, "date")) == "2000-01-01"
        # does not reset after continuation
        assert str(generated_rows.row_values(5, "date")) == "2000-02-05"
        assert str(generated_rows.row_values(11, "date")) == "2000-02-05"


class TestNumberCounterValidator:
    """Test validators for Counters.NumberCounter()"""

    def test_valid_default(self):
        """Test valid call with default parameters"""
        context = ValidationContext()
        sv = StructuredValue("Counters.NumberCounter", {}, "test.yml", 10)

        Counters.Validators.validate_NumberCounter(sv, context)

        assert len(context.errors) == 0
        assert len(context.warnings) == 0

    def test_valid_custom_start(self):
        """Test valid call with custom start"""
        context = ValidationContext()
        sv = StructuredValue("Counters.NumberCounter", {"start": 100}, "test.yml", 10)

        Counters.Validators.validate_NumberCounter(sv, context)

        assert len(context.errors) == 0

    def test_valid_custom_step(self):
        """Test valid call with custom step"""
        context = ValidationContext()
        sv = StructuredValue(
            "Counters.NumberCounter", {"start": 0, "step": 10}, "test.yml", 10
        )

        Counters.Validators.validate_NumberCounter(sv, context)

        assert len(context.errors) == 0

    def test_valid_negative_step(self):
        """Test valid call with negative step (countdown)"""
        context = ValidationContext()
        sv = StructuredValue(
            "Counters.NumberCounter", {"start": 100, "step": -5}, "test.yml", 10
        )

        Counters.Validators.validate_NumberCounter(sv, context)

        assert len(context.errors) == 0

    def test_valid_with_name(self):
        """Test valid call with name parameter"""
        context = ValidationContext()
        sv = StructuredValue(
            "Counters.NumberCounter",
            {"start": 1, "step": 1, "name": "my_counter"},
            "test.yml",
            10,
        )

        Counters.Validators.validate_NumberCounter(sv, context)

        assert len(context.errors) == 0

    def test_invalid_start_string(self):
        """Test error when start is a string"""
        context = ValidationContext()
        sv = StructuredValue("Counters.NumberCounter", {"start": "100"}, "test.yml", 10)

        Counters.Validators.validate_NumberCounter(sv, context)

        assert len(context.errors) >= 1
        assert any(
            "start" in err.message.lower() and "integer" in err.message.lower()
            for err in context.errors
        )

    def test_invalid_start_float(self):
        """Test error when start is a float"""
        context = ValidationContext()
        sv = StructuredValue("Counters.NumberCounter", {"start": 3.14}, "test.yml", 10)

        Counters.Validators.validate_NumberCounter(sv, context)

        assert len(context.errors) >= 1
        assert any(
            "start" in err.message.lower() and "integer" in err.message.lower()
            for err in context.errors
        )

    def test_invalid_step_string(self):
        """Test error when step is a string"""
        context = ValidationContext()
        sv = StructuredValue("Counters.NumberCounter", {"step": "5"}, "test.yml", 10)

        Counters.Validators.validate_NumberCounter(sv, context)

        assert len(context.errors) >= 1
        assert any(
            "step" in err.message.lower() and "integer" in err.message.lower()
            for err in context.errors
        )

    def test_invalid_step_float(self):
        """Test error when step is a float"""
        context = ValidationContext()
        sv = StructuredValue("Counters.NumberCounter", {"step": 2.5}, "test.yml", 10)

        Counters.Validators.validate_NumberCounter(sv, context)

        assert len(context.errors) >= 1
        assert any(
            "step" in err.message.lower() and "integer" in err.message.lower()
            for err in context.errors
        )

    def test_invalid_step_zero(self):
        """Test error when step is zero"""
        context = ValidationContext()
        sv = StructuredValue("Counters.NumberCounter", {"step": 0}, "test.yml", 10)

        Counters.Validators.validate_NumberCounter(sv, context)

        assert len(context.errors) >= 1
        assert any(
            "step" in err.message.lower() and "zero" in err.message.lower()
            for err in context.errors
        )

    def test_warning_name_not_string(self):
        """Test warning when name is not a string"""
        context = ValidationContext()
        sv = StructuredValue("Counters.NumberCounter", {"name": 123}, "test.yml", 10)

        Counters.Validators.validate_NumberCounter(sv, context)

        assert len(context.warnings) >= 1
        assert any(
            "name" in warn.message.lower() and "string" in warn.message.lower()
            for warn in context.warnings
        )

    def test_unknown_parameter_warning(self):
        """Test warning for unknown parameters"""
        context = ValidationContext()
        sv = StructuredValue(
            "Counters.NumberCounter",
            {"start": 1, "unknown_param": "value"},
            "test.yml",
            10,
        )

        Counters.Validators.validate_NumberCounter(sv, context)

        assert len(context.warnings) >= 1
        assert any(
            "unknown parameter" in warn.message.lower() for warn in context.warnings
        )

    def test_jinja_number_counter_valid(self):
        """Test NumberCounter called inline in Jinja template"""
        yaml = """
        - plugin: snowfakery.standard_plugins.Counters.Counters
        - var: counter
          value:
            Counters.NumberCounter:
              start: 100
              step: 5
        - object: Example
          fields:
            value: ${{counter.next()}}
        """
        result = generate_data(StringIO(yaml), validate_only=True)
        assert result.errors == []

    def test_jinja_number_counter_invalid(self):
        """Test NumberCounter with invalid step in Jinja"""
        yaml = """
        - plugin: snowfakery.standard_plugins.Counters.Counters
        - var: counter
          value:
            Counters.NumberCounter:
              step: 0
        """
        with pytest.raises(exc.DataGenValidationError) as e:
            generate_data(StringIO(yaml), validate_only=True)
        assert "step" in str(e.value).lower() and "zero" in str(e.value).lower()


class TestDateCounterValidator:
    """Test validators for Counters.DateCounter()"""

    def test_valid_today_daily(self):
        """Test valid call with today and daily increment"""
        context = ValidationContext()
        sv = StructuredValue(
            "Counters.DateCounter",
            {"start_date": "today", "step": "+1d"},
            "test.yml",
            10,
        )

        Counters.Validators.validate_DateCounter(sv, context)

        assert len(context.errors) == 0

    def test_valid_specific_date(self):
        """Test valid call with specific date"""
        context = ValidationContext()
        sv = StructuredValue(
            "Counters.DateCounter",
            {"start_date": "2024-01-01", "step": "+1w"},
            "test.yml",
            10,
        )

        Counters.Validators.validate_DateCounter(sv, context)

        assert len(context.errors) == 0

    def test_valid_monthly_increment(self):
        """Test valid call with monthly increment"""
        context = ValidationContext()
        sv = StructuredValue(
            "Counters.DateCounter",
            {"start_date": "today", "step": "+1M"},
            "test.yml",
            10,
        )

        Counters.Validators.validate_DateCounter(sv, context)

        assert len(context.errors) == 0

    def test_valid_negative_step(self):
        """Test valid call with negative step (decrement)"""
        context = ValidationContext()
        sv = StructuredValue(
            "Counters.DateCounter",
            {"start_date": "today", "step": "-1d"},
            "test.yml",
            10,
        )

        Counters.Validators.validate_DateCounter(sv, context)

        assert len(context.errors) == 0

    def test_valid_with_name(self):
        """Test valid call with name parameter"""
        context = ValidationContext()
        sv = StructuredValue(
            "Counters.DateCounter",
            {"start_date": "today", "step": "+1d", "name": "my_date_counter"},
            "test.yml",
            10,
        )

        Counters.Validators.validate_DateCounter(sv, context)

        assert len(context.errors) == 0

    def test_missing_start_date(self):
        """Test error when start_date is missing"""
        context = ValidationContext()
        sv = StructuredValue("Counters.DateCounter", {"step": "+1d"}, "test.yml", 10)

        Counters.Validators.validate_DateCounter(sv, context)

        assert len(context.errors) >= 1
        assert any(
            "missing" in err.message.lower() and "start_date" in err.message.lower()
            for err in context.errors
        )

    def test_missing_step(self):
        """Test error when step is missing"""
        context = ValidationContext()
        sv = StructuredValue(
            "Counters.DateCounter", {"start_date": "today"}, "test.yml", 10
        )

        Counters.Validators.validate_DateCounter(sv, context)

        assert len(context.errors) >= 1
        assert any(
            "missing" in err.message.lower() and "step" in err.message.lower()
            for err in context.errors
        )

    def test_invalid_step_not_string(self):
        """Test error when step is not a string"""
        context = ValidationContext()
        sv = StructuredValue(
            "Counters.DateCounter", {"start_date": "today", "step": 1}, "test.yml", 10
        )

        Counters.Validators.validate_DateCounter(sv, context)

        assert len(context.errors) >= 1
        assert any(
            "step" in err.message.lower() and "string" in err.message.lower()
            for err in context.errors
        )

    def test_invalid_step_format(self):
        """Test error when step has invalid format"""
        context = ValidationContext()
        sv = StructuredValue(
            "Counters.DateCounter",
            {"start_date": "today", "step": "invalid"},
            "test.yml",
            10,
        )

        Counters.Validators.validate_DateCounter(sv, context)

        assert len(context.errors) >= 1
        assert any(
            "step" in err.message.lower() and "format" in err.message.lower()
            for err in context.errors
        )

    def test_valid_step_formats(self):
        """Test all valid step formats"""
        valid_steps = ["+1d", "-1d", "+1w", "-1w", "+1M", "-1M", "+1y", "-1y", "+1w2d"]

        for step_val in valid_steps:
            context = ValidationContext()
            sv = StructuredValue(
                "Counters.DateCounter",
                {"start_date": "today", "step": step_val},
                "test.yml",
                10,
            )

            Counters.Validators.validate_DateCounter(sv, context)

            assert len(context.errors) == 0, f"Step format {step_val} should be valid"

    def test_warning_name_not_string(self):
        """Test warning when name is not a string"""
        context = ValidationContext()
        sv = StructuredValue(
            "Counters.DateCounter",
            {"start_date": "today", "step": "+1d", "name": 123},
            "test.yml",
            10,
        )

        Counters.Validators.validate_DateCounter(sv, context)

        assert len(context.warnings) >= 1
        assert any(
            "name" in warn.message.lower() and "string" in warn.message.lower()
            for warn in context.warnings
        )

    def test_unknown_parameter_warning(self):
        """Test warning for unknown parameters"""
        context = ValidationContext()
        sv = StructuredValue(
            "Counters.DateCounter",
            {"start_date": "today", "step": "+1d", "unknown": "value"},
            "test.yml",
            10,
        )

        Counters.Validators.validate_DateCounter(sv, context)

        assert len(context.warnings) >= 1
        assert any(
            "unknown parameter" in warn.message.lower() for warn in context.warnings
        )

    def test_jinja_date_counter_valid(self):
        """Test DateCounter called inline in Jinja template"""
        yaml = """
        - plugin: snowfakery.standard_plugins.Counters.Counters
        - var: date_counter
          value:
            Counters.DateCounter:
              start_date: today
              step: +1d
        - object: Example
          fields:
            date_value: ${{date_counter.next()}}
        """
        result = generate_data(StringIO(yaml), validate_only=True)
        assert result.errors == []

    def test_jinja_date_counter_missing_param(self):
        """Test DateCounter with missing required parameter in Jinja"""
        yaml = """
        - plugin: snowfakery.standard_plugins.Counters.Counters
        - var: counter
          value:
            Counters.DateCounter:
              start_date: today
        """
        with pytest.raises(exc.DataGenValidationError) as e:
            generate_data(StringIO(yaml), validate_only=True)
        assert "missing" in str(e.value).lower() and "step" in str(e.value).lower()


class TestCountersValidationIntegration:
    """Integration tests for Counters validation"""

    def test_both_counters_valid(self):
        """Test both counters in same recipe"""
        yaml = """
        - plugin: snowfakery.standard_plugins.Counters.Counters
        - var: num_counter
          value:
            Counters.NumberCounter:
              start: 100
              step: 5
        - var: date_counter
          value:
            Counters.DateCounter:
              start_date: "2024-01-01"
              step: +1d
        - object: Example
          fields:
            number: ${{num_counter.next()}}
            date: ${{date_counter.next()}}
        """
        result = generate_data(StringIO(yaml), validate_only=True)
        assert result.errors == []

    def test_multiple_errors(self):
        """Test multiple validation errors are caught"""
        yaml = """
        - plugin: snowfakery.standard_plugins.Counters.Counters
        - var: bad_num
          value:
            Counters.NumberCounter:
              step: 0
        - var: bad_date
          value:
            Counters.DateCounter:
              start_date: today
        """
        with pytest.raises(exc.DataGenValidationError) as e:
            generate_data(StringIO(yaml), validate_only=True)
        # Should catch both errors
        assert "step" in str(e.value).lower()

    def test_counters_with_jinja_inline(self):
        """Test counters created and used inline in Jinja"""
        yaml = """
        - plugin: snowfakery.standard_plugins.Counters.Counters
        - var: counter
          value:
            Counters.NumberCounter:
              start: 1
              step: 1
        - object: Example
          count: 5
          fields:
            sequence: ${{counter.next()}}
        """
        result = generate_data(StringIO(yaml), validate_only=True)
        assert result.errors == []
