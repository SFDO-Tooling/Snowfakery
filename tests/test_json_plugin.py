from io import StringIO
import json

from snowfakery.data_generator import generate


class TestJSONPlugin:
    def test_json_flat(self, generated_rows):
        yaml = """
            - plugin: snowfakery.standard_plugins.json.JSON

            - object: Flat
              fields:
                    abc:
                        JSON.object:
                            year: 2023
                            month: Nov
                            day: 3
                    def:
                        JSON.array:
                            - 1
                            - 2
                            - 3
        """
        continuation_file = StringIO()
        generate(StringIO(yaml), {}, generate_continuation_file=continuation_file)

        assert json.loads(generated_rows.row_values(0, "abc")) == {
            "year": 2023,
            "month": "Nov",
            "day": 3,
        }

    def test_json_nested(self, generated_rows):
        yaml = """
            - plugin: snowfakery.standard_plugins.json.JSON

            - object: Nested
              fields:
                nested:
                  JSON.object:
                    int: 3
                    array:
                      JSON.array:
                        - 1
                        - null
                        - 3.0
                        - true

        """

        continuation_file = StringIO()
        generate(StringIO(yaml), {}, generate_continuation_file=continuation_file)

        assert json.loads(generated_rows.row_values(0, "nested")) == {
            "int": 3,
            "array": [1, None, 3.0, True],
        }
