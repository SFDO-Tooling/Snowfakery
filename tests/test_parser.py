from io import StringIO

from datetime import date

import pytest

from snowfakery.parse_recipe_yaml import parse_recipe
from snowfakery import data_gen_exceptions as exc


class TestParseGenerator:
    def test_parser_simple(self):
        yamlstr = """
        - object: OBJ
          fields:
            date:
                date_between:
                    start_date: today
                    end_date: 2000-01-01
        """
        ParseResult = parse_recipe(StringIO(yamlstr))
        # useful for debugging if the test breaks!
        # print(yaml.dump(ParseResult.templates))

        assert ParseResult.options == []
        obj_template = ParseResult.templates[0]
        assert obj_template.tablename == "OBJ"
        assert obj_template.friends == []
        assert obj_template.fields[0].name == "date"
        assert obj_template.fields[0].definition.function_name == "date_between"
        assert (
            obj_template.fields[0].definition.kwargs["start_date"].definition == "today"
        )
        assert obj_template.fields[0].definition.kwargs["end_date"].definition == date(
            year=2000, month=1, day=1
        )

    def test_parser__no_dots_in_names__error(self):
        yamlstr = """
        - object: Foo
          nickname: Foo.bar
        """
        with pytest.warns(UserWarning, match="Foo.bar.*nickname.*"):
            parse_recipe(StringIO(yamlstr))

    def test_parse_alterate_indentations(self):
        yamlstr = """
        - object: Foo
          fields:
            npe01__PreferredPhone__c:
              if:
                - choice:
                    when: ${{HomePhone!=NULL}}
                    pick: Home
                - choice:
                    when: ${{MobilePhone!=NULL}}
                    pick: Mobile
                - choice:
                  when: ${{nnpe01__WorkPhone__c!=NULL}}
                  pick: Work
                - choice:
                    pick: NULL
        """
        out = parse_recipe(StringIO(yamlstr))
        assert len(out.templates[0].fields[0].definition.args) == 4

    def test_parser__error_structured_value_zero_fields(self):
        yamlstr = """
        - object: Foo
          fields:
            b: {}
        """
        with pytest.raises(exc.DataGenSyntaxError, match="Strange datastructure"):
            parse_recipe(StringIO(yamlstr))

    def test_parse_var_name_missing(self):
        yamlstr = """
- object: Outside
  fields:
    value: ${{the_var}}
    __the_other_var: 20
    the_other_value: ${{__the_other_var}}
  friends:
    - var:
      value: 12
        """
        with pytest.raises(exc.DataGenSyntaxError):
            parse_recipe(StringIO(yamlstr))

    def test_parser__weird_top_level(self):
        yamlstr = """
        - object: Foo
        - 5
        """
        with pytest.raises(exc.DataGenSyntaxError, match="Top level elements") as e:
            parse_recipe(StringIO(yamlstr))
            assert 5 in str(e.value)

    def test_parser__weird_top_level__2(self):
        yamlstr = """
        a: b
        c: d
        """
        with pytest.raises(
            exc.DataGenSyntaxError, match="Recipe file should be a list"
        ) as e:
            parse_recipe(StringIO(yamlstr))
            assert 5 in str(e.value)
