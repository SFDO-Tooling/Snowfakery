from io import StringIO
import unittest

from datetime import date

import pytest

from snowfakery.parse_recipe_yaml import parse_recipe


class TestParseGenerator(unittest.TestCase):
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
