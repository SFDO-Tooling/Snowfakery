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


class TestStructuredValues:
    def test_structured_values(self, generated_rows):
        generate(StringIO(structured_values_with_templates), {}, None)
        assert isinstance(generated_rows.mock_calls[0][1][1]["B"], int)
        assert 2 <= generated_rows.mock_calls[0][1][1]["B"] <= 8

    def test_lazy_random_choice(self, generated_rows):
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
        assert len(generated_rows.mock_calls) == 2, generated_rows.mock_calls
