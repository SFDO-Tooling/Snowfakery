from io import StringIO

from snowfakery.data_generator import generate


class TestExtraFakers:
    def test_non_profit(self, generated_rows):
        yaml = """
        - plugin: faker_nonprofit.Provider
        - object: OBJ
          fields:
            npo:
                fake: nonprofit_name
        """
        generate(StringIO(yaml))
        assert len(generated_rows.row_values(0, "npo"))

    def test_edu(self, generated_rows):
        yaml = """
        - plugin: faker_edu.Provider
        - object: OBJ
          fields:
            institution:
                fake: institution_name
        """
        generate(StringIO(yaml))
        assert len(generated_rows.row_values(0, "institution"))
