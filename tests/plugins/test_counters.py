from io import StringIO

import pytest

from snowfakery.api import generate_data
import snowfakery.data_gen_exceptions as exc


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
