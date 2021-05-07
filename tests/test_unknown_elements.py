from io import StringIO
import pytest

from snowfakery.data_generator import generate
from snowfakery.data_gen_exceptions import DataGenError


class TestFaker:
    def test_top_field_unknown(self):
        yaml = """
        - bobject: OBJ
          fields:
            first_name:
                fake:
                    first_name
        """
        with pytest.raises(DataGenError):
            generate(StringIO(yaml), {}, None)

    def test_secondary_field_unknown(self):
        yaml = """
        - object: OBJ
          bfields:
            first_name:
                fake:
                    first_name
        """
        with pytest.raises(DataGenError):
            generate(StringIO(yaml), {}, None)
