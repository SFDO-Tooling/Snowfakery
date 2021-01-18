from io import StringIO

import pytest

from snowfakery.data_generator import generate
from snowfakery.data_gen_exceptions import DataGenError


class TestFormulas:
    def test_simple_math_fields_not_ordered(self, generated_rows):
        yaml = """
        - object: XXX
          fields:
            total: ${{a + (b + c)}}
            a: 10
            b: 20
            c: 30
        """
        generate(StringIO(yaml), {})
        assert generated_rows.row_values(0, "total") == 60

    def test_simple_math_fields_nested_not_ordered(self, generated_rows):
        yaml = """
        - object: parent
          fields:
            a: 10
            total_obj:
              - object: total
                fields:
                  t: ${{parent.a + parent.b}}
            b: 20
        """
        generate(StringIO(yaml), {})
        assert generated_rows.row_values(0, "t") == 30

    def test_self_reference__error(self):
        yaml = """
        - object: XXX
          fields:
            a: XXX ${{a}} YYY
        """
        with pytest.raises(DataGenError, match="Field cycles detected"):
            generate(StringIO(yaml), {})

    def test_circular_references__error(self):
        yaml = """
        - object: XXX
          fields:
            a: XXX ${{(b)}} YYY
            b: XXX ${{(a+(a+b))}} YYY
        """
        with pytest.raises(DataGenError, match="Field cycles detected"):
            generate(StringIO(yaml), {})
