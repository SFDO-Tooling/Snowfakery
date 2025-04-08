from io import StringIO
from unittest import mock
import pydantic

from datetime import datetime, date

from snowfakery.data_generator import generate
from snowfakery.data_gen_exceptions import DataGenError

import pytest


def row_values(write_row_mock, index, value):
    return write_row_mock.mock_calls[index][1][1][value]


class TestTemplateFuncs:
    def test_inline_reference(self, generated_rows):
        yaml = """
        - object: Person
          nickname: daddy
          count: 1
        - object: Person
          count: 1
          fields:
            parent: ${{reference(daddy).id}}
            parent2: ${{reference(daddy)}}
        """
        generate(StringIO(yaml), {}, None)
        assert generated_rows.mock_calls == [
            mock.call("Person", {"id": 1}),
            mock.call("Person", {"id": 2, "parent": 1, "parent2": mock.ANY}),
        ]

    def test_unweighted_random_choice_object(self, generated_rows):
        yaml = """
        - object : Task
          fields:
            who:
                random_choice:
                  - object: Contact
                    fields:
                        FirstName: Bart
                        LastName: Simpson
                  - object: Lead
                    fields:
                        FirstName: Marge
                        LastName: Simpson
        """

        with mock.patch("random.choice", lambda x: x[-1]):
            generate(StringIO(yaml), {}, None)

            assert len(generated_rows.mock_calls) == 2, generated_rows.mock_calls

        assert generated_rows.mock_calls[0] == mock.call(
            "Lead", {"id": 1, "FirstName": "Marge", "LastName": "Simpson"}
        )

    def test_weighted_random_choice(self, generated_rows):
        yaml = """
        - object : A
          fields:
            b:
                random_choice:
                    - choice:
                        probability: 50%
                        pick:
                        - object: C
                    - choice:
                        probability: 40%
                        pick:
                        - object: D
                    - choice:
                        probability: 10%
                        pick:
                        - object: E
        """
        generate(StringIO(yaml), {}, None)
        assert len(generated_rows.mock_calls) == 2, generated_rows.mock_calls
        # TODO CHECK MORE

    def test_weighted_random_choice_strings(self, generated_rows):
        yaml = """
        - object : A
          fields:
            b:
                random_choice:
                    A: 80%
                    B: 10%
                    C: 10%
        """
        generate(StringIO(yaml))
        assert len(generated_rows.mock_calls) == 1, generated_rows.mock_calls

    def test_weighted_random_choice_strings_computed_percentages(self, generated_rows):
        yaml = """
        - object : A
          fields:
            __a_percent: 60
            b:
                random_choice:
                    A: ${{__a_percent}}%
                    B: ${{__a_percent / 2}}%
                    C: ${{100 - (__a_percent * 1.5)}}%
        """
        generate(StringIO(yaml))
        assert len(generated_rows.mock_calls) == 1, generated_rows.mock_calls

    def test_conditional_is_lazy(self, generated_rows):
        yaml = """
        - object : A
          fields:
            a:
                if:
                    - choice:
                        when: False
                        pick: ${{should_not_be_evaluated}}
                    - choice:
                        pick: BBB
        """
        generate(StringIO(yaml), {}, None)
        assert generated_rows.mock_calls == [mock.call("A", {"id": 1, "a": "BBB"})]

    def test_conditional(self, generated_rows):
        yaml = """
        - object : A
          fields:
            a: False
            b: True
            c: True
            d:
                if:
                    - choice:
                        when: ${{a}}
                        pick: AAA
                    - choice:
                        when: ${{b}}
                        pick: BBB
                    - choice:
                        when: ${{c}}
                        pick: CCC
        """
        generate(StringIO(yaml), {}, None)
        assert generated_rows.mock_calls == [
            mock.call("A", {"id": 1, "a": False, "b": True, "c": True, "d": "BBB"})
        ]

    def test_conditional_error(self, generated_rows):
        yaml = """
        - object : A
          fields:
            a:
                if:
                    - choice:
                        pick: AAA
                    - choice:
                        when: ${{b}}
                        pick: BBB
        """
        with pytest.raises(DataGenError) as e:
            generate(StringIO(yaml), {}, None)
        assert "when" in str(e.value)

    def test_conditional_fallthrough(self, generated_rows):
        yaml = """
        - object : A
          fields:
            x:
                if:
                    - choice:
                        when: False
                        pick: AAA
                    - choice:
                        pick: BBB
        """
        generate(StringIO(yaml), {}, None)
        assert generated_rows.mock_calls == [mock.call("A", {"id": 1, "x": "BBB"})]

    def test_conditional_nested(self, generated_rows):
        yaml = """
        - object : A
          fields:
            a: True
            b: False
            c: True
            x:
                if:
                    - choice:
                        when: ${{a}}
                        pick:
                          if:
                            - choice:
                                when: ${{b}}
                                pick: BBB
                            - choice:
                                when: ${{c}}
                                pick: CCC
                    - choice:
                        pick: DDD
        """
        generate(StringIO(yaml), {}, None)
        assert generated_rows.mock_calls[0][1][1]["x"] == "CCC"

    def test_parse_date_from_datetime_string(self, generated_rows):
        yaml = """
        - object : A
          fields:
            a: ${{date("2012-01-01T00:01")}}
        """
        generate(StringIO(yaml), {}, None)
        assert generated_rows.mock_calls[0][1][1]["a"] == "2012-01-01"

    def test_parse_date_from_date_string(self, generated_rows):
        yaml = """
        - object : A
          fields:
            a: ${{date("2012-01-01")}}
        """
        generate(StringIO(yaml), {}, None)
        assert generated_rows.mock_calls[0][1][1]["a"] == "2012-01-01"

    def test_date_from_datetime(self, generated_rows):
        yaml = """
        - object : A
          fields:
            a: ${{date(datetime(year=2012, month=1, day=1))}}
        """
        generate(StringIO(yaml), {}, None)
        assert generated_rows.mock_calls[0][1][1]["a"] == "2012-01-01"

    def test_now_variable(self, generated_rows):
        yaml = """
        - object : A
          fields:
            a: ${{now}}
            b: ${{now}}
        """
        generate(StringIO(yaml), {}, None)
        assert datetime.fromisoformat(generated_rows.table_values("A", 0, "a"))
        assert datetime.fromisoformat(generated_rows.table_values("A", 0, "b"))

    @mock.patch("snowfakery.data_generator_runtime.datetime")
    def test_now_calls_datetime_now(self, datetime):
        now = datetime.now = mock.Mock()
        yaml = """
        - object : A
          fields:
            a: ${{now}}
            b: ${{now}}
            c: ${{now}}
        """
        generate(StringIO(yaml))
        assert len(now.mock_calls) == 3

    def test_old_syntax(self, generated_rows):
        yaml = """
        - object : A
          fields:
            a: ${{5 + 3}}
        """
        generate(StringIO(yaml), {}, None)
        assert generated_rows.mock_calls[0][1][1]["a"] == 8

    def test_functions_inline(self, generated_rows):
        yaml = """
        - object : A
          fields:
            wedding: Our wedding date is ${{date_between(start_date="2012-01-31", end_date="2012-12-31")}}
            number: The number is ${{random_number(min=15, max=19)}}
        """
        generate(StringIO(yaml), {}, None)
        assert "2012" in generated_rows.mock_calls[0][1][1]["wedding"]
        assert "1" in generated_rows.mock_calls[0][1][1]["number"]

    def test_date_between_error_handling(self, generated_rows):
        yaml = """
        - object : A
          fields:
            date:
                date_between:
                    start_date: "2040-13-13"
                    end_date: "2040-13-13"
        """
        with pytest.raises(DataGenError):
            generate(StringIO(yaml), {}, None)

    def test_child_index(self, generated_rows):
        yaml = """
        - object: A
          friends:
            - object: B
              count: 3
              fields:
                    num: ${{child_index}}
        """
        generate(StringIO(yaml), {}, None)
        assert generated_rows.mock_calls[3][1][1]["num"] == 2

    def test_random_number_with_step(self, generated_rows):
        yaml = """
        - object : A
          fields:
            number: ${{random_number(min=15, max=200, step=5)}}
        """
        generate(StringIO(yaml), {}, None)
        assert 15 <= int(generated_rows.row_values(0, "number")) <= 200
        assert int(generated_rows.row_values(0, "number")) % 5 == 0

    def test_random_number_with_step_odd(self, generated_rows):
        yaml = """
        - object : A
          fields:
            number: ${{random_number(min=12, max=22, step=5)}}
        """
        generate(StringIO(yaml), {}, None)
        assert int(generated_rows.row_values(0, "number")) in (12, 17, 22)

    def test_random_choice_error_args_and_kwargs(self):
        yaml = """
        - object: A
          fields:
            num: ${{random_choice(1,2,a=10,b=20)}}
        """
        with pytest.raises(DataGenError):
            generate(StringIO(yaml))

    def test_random_choice_error_no_choices(self, generated_rows):
        yaml = """
        - object: A
          fields:
            num: ${{random_choice()}}
        """
        with pytest.raises(DataGenError):
            generate(StringIO(yaml))

    def test_random_choice_can_generate_None(self, generated_rows):
        yaml = """
        - object: A
          fields:
            void:
                random_choice:
                    -
                    -
        """
        generate(StringIO(yaml))
        generated_rows.mock_calls[0][1][1]["void"] is None

    def test_if_error_no_choices(self, generated_rows):
        yaml = """
        - object: A
          fields:
            num: ${{if()}}
        """
        with pytest.raises(DataGenError):
            generate(StringIO(yaml))

    def test_template_context(self, generated_rows):
        yaml = """
        - var: V
          value: ${{snowfakery_filename}}
        - object: foo
          fields:
            filename: ${{template.filename}}
            filename2: ${{snowfakery_filename}}
            filename3: ${{V}}
            template_id: ${{template.id}}
        """
        generate(StringIO(yaml))
        assert generated_rows.table_values("foo", 1, "filename") == "<stream>"
        assert generated_rows.table_values("foo", 1, "filename2") == "<stream>"
        assert generated_rows.table_values("foo", 1, "filename3") == "<stream>"
        assert int(generated_rows.table_values("foo", 1, "template_id"))

    def test_null(self, generated_rows):
        yaml = """
        - object: foo
          count: 5
          fields:
            EndDate:
                if:
                    - choice:
                        when: ${{ child_index%2==0 }}
                        pick: 1
                    - choice:
                        pick: NULL
            DateSupplied:
                if:
                    - choice:
                        when: ${{ EndDate!=NULL }}
                        pick: "Yes"
                    - choice:
                        pick: "No"
        """
        generate(StringIO(yaml))
        call = mock.call
        assert generated_rows.mock_calls == [
            call(
                "foo",
                {"id": 1, "EndDate": 1, "DateSupplied": "Yes"},
            ),
            call("foo", {"id": 2, "EndDate": None, "DateSupplied": "No"}),
            call(
                "foo",
                {"id": 3, "EndDate": 1, "DateSupplied": "Yes"},
            ),
            call("foo", {"id": 4, "EndDate": None, "DateSupplied": "No"}),
            call(
                "foo",
                {"id": 5, "EndDate": 1, "DateSupplied": "Yes"},
            ),
        ]

    def test_random_choice_nonstring_keys(self, generated_rows):
        with open("tests/random_choice.yml") as yaml:
            generate(yaml)
        result = generated_rows.table_values("foo", 0)

        class ResultModel(pydantic.v1.BaseModel):
            id: int
            bool: bool
            date: date

        assert ResultModel(**result)

    def test_random_choice_wrong_type_keys(self, generated_rows):
        with open("tests/bad_random_choice_keys.yml") as yaml:
            with pytest.raises(DataGenError) as e:
                generate(yaml)
        assert "null" in str(e.value)

    def test_debug(self, capsys):
        yaml = """
        - object : A
          fields:
            a: ${{debug("XYZZY")}}
            b: ${{debug(420)}}
        """
        generate(StringIO(yaml))
        stderr = capsys.readouterr().err
        assert "XYZZY" in stderr
        assert "420" in stderr
