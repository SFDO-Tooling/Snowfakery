from io import StringIO
import unittest

from snowfakery.parse_factory_yaml import parse_factory
from snowfakery.data_generator import generate
from snowfakery.data_gen_exceptions import DataGenSyntaxError, DataGenValueError

yaml = """                              #1
- object: A                             #2
  count: 10                             #3
  fields:                               #4
    A: What a wonderful life            #5
    X: Y                                #6
- object: B                             #7
  count: <<expr>>                       #8
  fields:                               #9
    A: What a wonderful life            #10
    X: Y                                #11
"""

yaml_with_syntax_error = """            #1
- object: A                             #2
  count: 10                             #3
  fields:                               #4
    A: What a wonderful life            #5
    X: Y                                #6
- object: B                             #7
  count: <<expr)>                       #8
  fields:                               #9
    A: What a wonderful life            #10
    X: Y                                #11
"""


class TestLineNumbers(unittest.TestCase):
    def test_line_numbers(self):
        result = parse_factory(StringIO(yaml))
        templates = result.templates
        assert templates[0].line_num == 2
        assert templates[0].fields[0].definition.line_num == 5
        line_num = templates[0].fields[1].definition.line_num
        assert 4 <= line_num <= 6  # anywhere in here is okay for small strings
        assert templates[1].count_expr.line_num == 8

    def test_value_error_reporting(self):
        with self.assertRaises(DataGenValueError) as e:
            generate(StringIO(yaml), {}, None)
        assert str(e.exception)[-2:] == ":8"

    def test_syntax_error_number_reporting(self):
        with self.assertRaises(DataGenSyntaxError) as e:
            generate(StringIO(yaml_with_syntax_error), {})
        assert str(e.exception)[-2:] == ":8"
