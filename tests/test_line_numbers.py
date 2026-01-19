from io import StringIO
import pytest
from snowfakery.parse_recipe_yaml import parse_recipe
from snowfakery.data_generator import generate
from snowfakery.data_gen_exceptions import DataGenSyntaxError, DataGenValueError

yaml = """                              #1
- snowfakery_version: 2                 #2
- object: A                             #3
  count: 10                             #4
  fields:                               #5
    A: What a wonderful life            #6
    X: Y                                #7
- object: B                             #8
  count: ${{expr}}                       #9
  fields:                               #10
    A: What a wonderful life            #11
    X: Y                                #12
"""

yaml_with_syntax_error = """            #1
- object: A                             #2
  count: 10                             #3
  fields:                               #4
    A: What a wonderful life            #5
    X: Y                                #6
- object: B                             #7
  count: ${{expr)>                       #8
  fields:                               #9
    A: What a wonderful life            #10
    X: Y                                #11
"""


class TestLineNumbers:
    def test_line_numbers(self):
        result = parse_recipe(StringIO(yaml))
        templates = result.templates
        assert templates[0].line_num == 3
        assert templates[0].fields[0].definition.line_num == 6
        line_num = templates[0].fields[1].definition.line_num
        assert 5 <= line_num <= 7  # anywhere in here is okay for small strings
        assert templates[1].count_expr.line_num == 9

    def test_value_error_reporting(self):
        with pytest.raises(DataGenValueError) as e:
            generate(StringIO(yaml), {}, None)
        assert str(e.value)[-2:] == ":9"

    def test_syntax_error_number_reporting(self):
        with pytest.raises(DataGenSyntaxError) as e:
            generate(StringIO(yaml_with_syntax_error), {})
        assert str(e.value)[-2:] == ":8"
