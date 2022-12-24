from io import StringIO


from snowfakery.data_generator import generate

structured_values_with_templates = """  #1
- object: A                             #2
  fields:                               #4
    A: 5                                 #5
    B:                                  #5
     random_number:                      #6
       min: ${{this.A - 3}}                      #7
       max: ${{this.A + 3}}                      #7
"""


write_row_path = "snowfakery.output_streams.SimpleFileOutputStream.write_row"


class TestStructuredValues:
    def test_structured_values(self, write_row):
        generate(StringIO(structured_values_with_templates), {}, None)
        assert isinstance(write_row.mock_calls[0][1][1]["B"], int)
        assert 2 <= write_row.mock_calls[0][1][1]["B"] <= 8

    def test_lazy_random_choice(self, write_row):
        yaml = """
        - object : A
          fields:
            b:
                random_choice:
                    - object: C
                    - object: D
                    - object: E
        """
        generate(StringIO(yaml), {}, None)
        assert len(write_row.mock_calls) == 2, write_row.mock_calls
