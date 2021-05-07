from io import StringIO
import pytest

from snowfakery.data_generator import generate
from snowfakery.data_gen_exceptions import (
    DataGenSyntaxError,
    DataGenNameError,
    DataGenError,
)

yaml1 = """                             #1
- object: A                             #2
  count: ${{abcd()}}                     #3
  fields:                               #4
    A: What a wonderful life            #5
    X: Y                                #6
    """

yaml2 = """- object: B                  #1
  count: ${{expr)>                       #2
  fields:                               #3
    A: What a wonderful life            #4
    X: Y                                #5
"""

yaml3 = """
- object: B                             #2
  count: 5                              #3
  fields:                               #4
    A: What a wonderful life            #5
    X:                                  #6
        xyzzy: abcde                    #7
"""


class TestErrors:
    def test_name_error(self):
        with pytest.raises(DataGenNameError) as e:
            generate(StringIO(yaml1), {}, None)
        assert str(e.value)[-2:] == ":3"

    def test_syntax_error(self):
        with pytest.raises(DataGenSyntaxError) as e:
            generate(StringIO(yaml2), {}, None)
        assert str(e.value)[-2:] == ":2"

    def test_funcname_error(self):
        with pytest.raises(DataGenError) as e:
            generate(StringIO(yaml3))
        assert "xyzzy" in str(e.value)
        assert e.value.line_num >= 5

    def test_conflicting_declarations_error(self):
        yaml = """
        - object: B                             #2
          macro: C                              #3
          fields:                               #4
            A: What a wonderful life            #5
            X:                                  #6
                xyzzy: abcde                    #7
        """
        with pytest.raises(DataGenError) as e:
            generate(StringIO(yaml))
        assert 4 > e.value.line_num >= 2

    def test_extra_keys(self):
        yaml = """
        - object: B                             #2
          velcro: C                             #3
          fields:                               #4
            A: What a wonderful life            #5
            X:                                  #6
                xyzzy: abcde                    #7
        """
        with pytest.raises(DataGenError) as e:
            generate(StringIO(yaml))
        assert 4 > e.value.line_num >= 2

    def test_missing_param(self):
        yaml = """
            - object: Person
              count: 5
              fields:
                gender: Male
                name:
                    fake:
        """
        with pytest.raises(DataGenError) as e:
            generate(StringIO(yaml))
        assert "Cannot evaluate function" in str(e.value)
        assert ":6" in str(e.value)

    def test_yaml_error(self):
        yaml = """
        - object: B                             #2
            velcro: C                             #3
        """
        with pytest.raises(DataGenSyntaxError) as e:
            generate(StringIO(yaml), {}, None)
        assert str(e.value)[-2:] == ":3"
