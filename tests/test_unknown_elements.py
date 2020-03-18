from io import StringIO
import unittest

from snowfakery.data_generator import generate
from snowfakery.data_gen_exceptions import DataGenError


class TestFaker(unittest.TestCase):
    def test_top_field_unknown(self):
        yaml = """
        - bobject: OBJ
          fields:
            first_name:
                fake:
                    first_name
        """
        with self.assertRaises(DataGenError):
            generate(StringIO(yaml), {}, None)

    def test_secondary_field_unknown(self):
        yaml = """
        - object: OBJ
          bfields:
            first_name:
                fake:
                    first_name
        """
        with self.assertRaises(DataGenError):
            generate(StringIO(yaml), {}, None)
