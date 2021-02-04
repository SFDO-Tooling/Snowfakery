from io import StringIO
from unittest import mock

from snowfakery.data_generator import generate
from snowfakery.data_gen_exceptions import DataGenError

import pytest

write_row_path = "snowfakery.output_streams.DebugOutputStream.write_row"


def row_values(write_row_mock, index, value):
    return write_row_mock.mock_calls[index][1][1][value]


class TestTemplateFuncs:
    @mock.patch(write_row_path)
    def test_inline_reference(self, write_row_mock):
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
        assert write_row_mock.mock_calls == [
            mock.call("Person", {"id": 1}),
            mock.call("Person", {"id": 2, "parent": 1, "parent2": mock.ANY}),
        ]

    @mock.patch(write_row_path)
    def test_unweighted_random_choice_object(self, write_row):
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

            assert len(write_row.mock_calls) == 2, write_row.mock_calls

        assert write_row.mock_calls[0] == mock.call(
            "Lead", {"id": 1, "FirstName": "Marge", "LastName": "Simpson"}
        )

    @mock.patch(write_row_path)
    def test_weighted_random_choice(self, write_row):
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
        assert len(write_row.mock_calls) == 2, write_row.mock_calls
        # TODO CHECK MORE

    @mock.patch(write_row_path)
    def test_weighted_random_choice_strings(self, write_row):
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
        assert len(write_row.mock_calls) == 1, write_row.mock_calls

    @mock.patch(write_row_path)
    def test_weighted_random_choice_strings_computed_percentages(self, write_row):
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
        assert len(write_row.mock_calls) == 1, write_row.mock_calls

    @mock.patch(write_row_path)
    def test_conditional_is_lazy(self, write_row):
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
        assert write_row.mock_calls == [mock.call("A", {"id": 1, "a": "BBB"})]

    @mock.patch(write_row_path)
    def test_conditional(self, write_row):
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
        assert write_row.mock_calls == [
            mock.call("A", {"id": 1, "a": False, "b": True, "c": True, "d": "BBB"})
        ]

    @mock.patch(write_row_path)
    def test_conditional_error(self, write_row):
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

    @mock.patch(write_row_path)
    def test_conditional_fallthrough(self, write_row):
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
        assert write_row.mock_calls == [mock.call("A", {"id": 1, "x": "BBB"})]

    @mock.patch(write_row_path)
    def test_conditional_nested(self, write_row):
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
        assert write_row.mock_calls[0][1][1]["x"] == "CCC"

    @mock.patch(write_row_path)
    def test_parse_date_from_datetime_string(self, write_row):
        yaml = """
        - object : A
          fields:
            a: <<date("2012-01-01T00:01")>>
        """
        generate(StringIO(yaml), {}, None)
        assert write_row.mock_calls[0][1][1]["a"] == "2012-01-01"

    @mock.patch(write_row_path)
    def test_parse_date_from_date_string(self, write_row):
        yaml = """
        - object : A
          fields:
            a: ${{date("2012-01-01")}}
        """
        generate(StringIO(yaml), {}, None)
        assert write_row.mock_calls[0][1][1]["a"] == "2012-01-01"

    @mock.patch(write_row_path)
    def test_date_from_datetime(self, write_row):
        yaml = """
        - object : A
          fields:
            a: ${{date(datetime(year=2012, month=1, day=1))}}
        """
        generate(StringIO(yaml), {}, None)
        assert write_row.mock_calls[0][1][1]["a"] == "2012-01-01"

    @mock.patch(write_row_path)
    def test_old_syntax(self, write_row):
        yaml = """
        - object : A
          fields:
            a: <<5 + 3>>
        """
        generate(StringIO(yaml), {}, None)
        assert write_row.mock_calls[0][1][1]["a"] == 8

    @mock.patch(write_row_path)
    def test_functions_inline(self, write_row):
        yaml = """
        - object : A
          fields:
            wedding: Our wedding date is ${{date_between(start_date="2012-01-31", end_date="2012-12-31")}}
            number: The number is ${{random_number(min=15, max=19)}}
        """
        generate(StringIO(yaml), {}, None)
        assert "2012" in write_row.mock_calls[0][1][1]["wedding"]
        assert "1" in write_row.mock_calls[0][1][1]["number"]

    @mock.patch(write_row_path)
    def test_date_between_error_handling(self, write_row):
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

    @mock.patch(write_row_path)
    def test_child_index(self, write_row):
        yaml = """
        - object: A
          friends:
            - object: B
              count: 3
              fields:
                    num: <<child_index>>
        """
        generate(StringIO(yaml), {}, None)
        assert write_row.mock_calls[3][1][1]["num"] == 2

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

    @mock.patch(write_row_path)
    def test_random_choice_error_no_choices(self, write_row):
        yaml = """
        - object: A
          fields:
            num: ${{random_choice()}}
        """
        with pytest.raises(DataGenError):
            generate(StringIO(yaml))

    @mock.patch(write_row_path)
    def test_random_choice_can_generate_None(self, write_row):
        yaml = """
        - object: A
          fields:
            void:
                random_choice:
                    -
                    -
        """
        generate(StringIO(yaml))
        write_row.mock_calls[0][1][1]["void"] is None

    @mock.patch(write_row_path)
    def test_if_error_no_choices(self, write_row):
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
